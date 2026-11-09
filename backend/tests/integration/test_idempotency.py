"""T14 -- idempotencia de decisiones humanas (AC-10, BR-15) y rechazo
humano de punta a punta (AC-11, BR-14/BR-16).

BR-15 solo es observable si el grafo sigue pausado despues de aplicar una
decision -- por eso AC-10 se ejercita via `OBSERVE` (BR-14: "mantiene el
caso en pausa"), que permite reenviar el mismo `decision_id` una segunda
vez sin que el grafo ya haya terminado."""

import uuid
from datetime import UTC, datetime

from langgraph.types import Command

from app.domain.enums import DecisionAction, Outcome, ReasonCode
from app.graph.build import build_graph
from app.graph.checkpointer import checkpointer_context
from app.graph.state import QuoteState

_S3_TEXT = (
    "Requerimos 60 arneses AR-450 de cuerpo entero para el proyecto de "
    "Arequipa, entrega para fin de mes."
)
_S4_TEXT = (
    "Necesito 40 pares de botas BT-900 para Trujillo. "
    "Nos pueden dar 10% de descuento por el volumen?"
)


def _decision(
    decision_id: str,
    action: DecisionAction,
    actor: str = "jefe.ventas",
    comment: str | None = None,
) -> dict:
    return {
        "decision_id": decision_id,
        "action": action.value,
        "actor": actor,
        "comment": comment,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def test_ac10_resubmitting_the_same_decision_id_produces_no_additional_effect() -> None:
    """BR-15: reenviar un decision_id ya aplicado en el mismo thread_id no
    produce efecto adicional -- se verifica que `applied_decision_ids` no
    crece con el reenvio, y que una decision genuinamente nueva si se
    aplica con normalidad despues."""
    thread_id = f"test-t14-idem-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        state = QuoteState(thread_id=thread_id, customer_id="FER-1001", raw_text=_S3_TEXT)
        paused = await graph.ainvoke(state, config=config)
        assert "__interrupt__" in paused

        decision_id = f"dec-idem-{uuid.uuid4()}"
        observe = _decision(
            decision_id, DecisionAction.OBSERVE, comment="Falta validar con el cliente."
        )

        first = await graph.ainvoke(Command(resume=observe), config=config)
        assert "__interrupt__" in first  # OBSERVE vuelve a pausar (BR-14)
        snapshot_1 = await graph.aget_state(config)
        assert snapshot_1.values["applied_decision_ids"] == [decision_id]

        # Reenvio exacto del mismo decision_id -- simula un doble clic o un
        # reintento de red sobre la misma decision.
        second = await graph.ainvoke(Command(resume=observe), config=config)
        assert "__interrupt__" in second
        snapshot_2 = await graph.aget_state(config)

        # BR-15: ningun efecto adicional. Sigue con una sola entrada, no dos.
        assert snapshot_2.values["applied_decision_ids"] == [decision_id]

        # Una decision nueva y distinta si se aplica con normalidad.
        approve_id = f"dec-final-{uuid.uuid4()}"
        approve = _decision(approve_id, DecisionAction.APPROVE)
        resumed = await graph.ainvoke(Command(resume=approve), config=config)

        assert resumed["outcome"] == Outcome.DRAFT_READY
        final_snapshot = await graph.aget_state(config)
        assert final_snapshot.values["applied_decision_ids"] == [decision_id, approve_id]


async def test_ac10_resubmission_returns_the_same_state_not_a_divergent_one() -> None:
    """Segunda parte de BR-15 -- "devuelve el estado existente": outcome,
    cotizacion y el punto de pausa deben ser identicos antes y despues de
    reenviar el mismo decision_id."""
    thread_id = f"test-t14-idem-state-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        state = QuoteState(thread_id=thread_id, customer_id="FER-1001", raw_text=_S3_TEXT)
        await graph.ainvoke(state, config=config)

        decision_id = f"dec-repeat-{uuid.uuid4()}"
        observe = _decision(decision_id, DecisionAction.OBSERVE)

        await graph.ainvoke(Command(resume=observe), config=config)
        snapshot_1 = await graph.aget_state(config)

        await graph.ainvoke(Command(resume=observe), config=config)
        snapshot_2 = await graph.aget_state(config)

        # `outcome` esta ausente en ambas -- el grafo nunca paso por
        # `finalize` (sigue pausado en human_approval), asi que su clave ni
        # siquiera existe en `values` (mismo comportamiento que en `result`
        # cuando el grafo interrumpe: ver test_scenarios.py).
        assert "outcome" not in snapshot_1.values
        assert "outcome" not in snapshot_2.values
        assert snapshot_1.values["quote"] == snapshot_2.values["quote"]
        assert snapshot_1.next == snapshot_2.next == ("human_approval",)


async def test_br15_reused_decision_id_cannot_change_the_action_at_graph_level() -> None:
    """Defensa en profundidad bajo la API: un decision_id ya aplicado no tiene
    efecto aunque llegue con otra accion. El caso sigue pausado y la ultima
    decision registrada no cambia."""
    thread_id = f"test-idem-action-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        state = QuoteState(thread_id=thread_id, customer_id="FER-1001", raw_text=_S3_TEXT)
        await graph.ainvoke(state, config=config)

        decision_id = f"dec-reused-{uuid.uuid4()}"
        await graph.ainvoke(
            Command(resume=_decision(decision_id, DecisionAction.OBSERVE)), config=config
        )
        result = await graph.ainvoke(
            Command(resume=_decision(decision_id, DecisionAction.APPROVE, actor="otro")),
            config=config,
        )

        assert "__interrupt__" in result
        snapshot = await graph.aget_state(config)
        assert snapshot.next == ("human_approval",)
        assert snapshot.values["human_decision"].action == DecisionAction.OBSERVE
        assert snapshot.values["human_decision"].actor == "jefe.ventas"
        assert snapshot.values["applied_decision_ids"] == [decision_id]
        assert snapshot.values.get("draft") is None


async def test_ac11_human_rejection_reaches_rejected_by_policy_with_audit() -> None:
    """AC-11: REJECT sobre un caso pendiente de aprobacion (S4, excepcion de
    descuento) termina en REJECTED_BY_POLICY, conservando el motivo original
    y con el actor auditado (BR-14, BR-16)."""
    thread_id = f"test-t14-ac11-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        state = QuoteState(thread_id=thread_id, customer_id="FER-1003", raw_text=_S4_TEXT)
        paused = await graph.ainvoke(state, config=config)
        assert "__interrupt__" in paused

        snapshot = await graph.aget_state(config)
        original_reasons = {r.reason_code for r in snapshot.values["approval_reasons"]}
        assert original_reasons == {ReasonCode.DISCOUNT_EXCEPTION}

        reject = _decision(
            f"dec-reject-{uuid.uuid4()}",
            DecisionAction.REJECT,
            actor="jefe.ventas",
            comment="Descuento fuera de politica, no se autoriza.",
        )
        resumed = await graph.ainvoke(Command(resume=reject), config=config)

        assert "__interrupt__" not in resumed
        assert resumed["outcome"] == Outcome.REJECTED_BY_POLICY
        assert resumed["reason_code"] == ReasonCode.DISCOUNT_EXCEPTION

        messages = [event.message for event in resumed["audit_log"]]
        assert any("jefe.ventas" in msg for msg in messages)
        assert any(event.node == "finalize" for event in resumed["audit_log"])
