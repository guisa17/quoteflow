"""T13 -- reanudacion durable tras un reinicio real del proceso (AC-09).

Distinto de test_checkpointer.py (T11) y test_scenarios.py (T12): esas
pruebas interrumpen y reanudan sobre la MISMA instancia de grafo, dentro
del mismo bloque `async with`. Eso no demuestra reanudacion durable -- solo
que `interrupt()` + `Command(resume=...)` funcionan dentro de un mismo
proceso. Aqui se descarta la instancia del grafo y del checkpointer por
completo entre interrumpir y reanudar, y se reconstruyen desde cero -- la
unica forma de probar que lo necesario para reanudar vive en Postgres, no
en memoria de Python."""

import uuid
from datetime import UTC, datetime

from langgraph.types import Command

from app.domain.enums import DecisionAction, Outcome
from app.graph.build import build_graph
from app.graph.checkpointer import checkpointer_context
from app.graph.state import QuoteState

_S3_TEXT = (
    "Requerimos 60 arneses AR-450 de cuerpo entero para el proyecto de "
    "Arequipa, entrega para fin de mes."
)


async def test_resumes_to_draft_ready_after_discarding_and_rebuilding_the_graph() -> None:
    """AC-09: interrumpir, descartar la instancia del grafo y reconstruirla
    simulando un reinicio, reanudar con el mismo thread_id, llegar a
    DRAFT_READY."""
    thread_id = f"test-t13-restart-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    # --- "Antes del reinicio": arranca, interrumpe, el proceso se cae. ---
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        state = QuoteState(thread_id=thread_id, customer_id="FER-1001", raw_text=_S3_TEXT)
        paused = await graph.ainvoke(state, config=config)
        assert "__interrupt__" in paused
    # El bloque `async with` cierra la conexion aqui; `graph` y `checkpointer`
    # quedan sin usarse. Es la simulacion mas fiel posible de un reinicio del
    # proceso sin levantar de verdad un segundo proceso del sistema operativo.
    del graph
    del checkpointer

    # --- "Despues del reinicio": checkpointer nuevo, grafo nuevo, mismo thread_id. ---
    async with checkpointer_context() as checkpointer_after:
        graph_after = build_graph(checkpointer_after)

        # El estado interrumpido debe seguir ahi, leido por una instancia
        # que nunca lo escribio.
        snapshot = await graph_after.aget_state(config)
        assert snapshot.next == ("human_approval",)

        decision_payload = {
            "decision_id": f"dec-t13-{uuid.uuid4()}",
            "action": DecisionAction.APPROVE.value,
            "actor": "jefe.ventas",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        resumed = await graph_after.ainvoke(Command(resume=decision_payload), config=config)

        assert resumed["outcome"] == Outcome.DRAFT_READY
        assert resumed["draft"] is not None
        assert resumed["applied_decision_ids"] == [decision_payload["decision_id"]]


async def test_resumed_execution_preserves_full_audit_trail_across_the_restart() -> None:
    """El audit_log acumulado antes del reinicio (ingest..evaluate_policy)
    debe seguir presente despues de reanudar sobre una instancia nueva --
    RF-08 exige un registro comprensible de la ejecucion completa, no solo
    de lo que paso despues de reanudar."""
    thread_id = f"test-t13-audit-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        state = QuoteState(thread_id=thread_id, customer_id="FER-1001", raw_text=_S3_TEXT)
        await graph.ainvoke(state, config=config)

    async with checkpointer_context() as checkpointer_after:
        graph_after = build_graph(checkpointer_after)
        pre_resume_snapshot = await graph_after.aget_state(config)
        nodes_before_resume = {event.node for event in pre_resume_snapshot.values["audit_log"]}
        assert "evaluate_policy" in nodes_before_resume

        decision_payload = {
            "decision_id": f"dec-audit-{uuid.uuid4()}",
            "action": DecisionAction.APPROVE.value,
            "actor": "jefe.ventas",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        resumed = await graph_after.ainvoke(Command(resume=decision_payload), config=config)

        nodes_after_resume = {event.node for event in resumed["audit_log"]}
        assert nodes_before_resume.issubset(nodes_after_resume)
        assert "human_approval" in nodes_after_resume
        assert "finalize" in nodes_after_resume
