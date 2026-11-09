"""T12 -- los 8 escenarios del seed, extremo a extremo contra Postgres real
(AC-01..AC-08). A diferencia de test_checkpointer.py (T11, que solo probo S1
y S3 como humo), aqui se ejercitan los 8, comparando `outcome` y
`reason_code` exactos -- es la cobertura sistematica que el DoD de T12 exige.

Cinco escenarios (S1, S2, S5, S6, S8) llegan a un estado terminal en la
primera invocacion. Los otros tres (S3, S4, S7) requieren aprobacion humana:
el grafo interrumpe en `human_approval` y `outcome` nunca se fija -- eso
es responsabilidad de `finalize`, que no se alcanza hasta que exista una
decision (T13/T14). Aqui se verifica que interrumpen con los motivos de
aprobacion correctos, no que terminan."""

import json
import uuid
from pathlib import Path

import pytest

from app.domain.enums import Outcome, ReasonCode
from app.graph.build import build_graph
from app.graph.checkpointer import checkpointer_context
from app.graph.state import QuoteState

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"
_SCENARIOS = {
    s["id"]: s for s in json.loads((_DATA_DIR / "sample_requests.json").read_text(encoding="utf-8"))
}


def _scenario(prefix: str) -> dict:
    for key, value in _SCENARIOS.items():
        if key.startswith(prefix):
            return value
    raise KeyError(prefix)


async def _run(scenario: dict) -> tuple[dict, str]:
    thread_id = f"test-{scenario['id']}-{uuid.uuid4()}"
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        state = QuoteState(
            thread_id=thread_id,
            customer_id=scenario["customer_id"],
            raw_text=scenario["raw_text"],
        )
        result = await graph.ainvoke(state, config=config)
        return result, thread_id


# (prefijo del escenario, Outcome esperado, ReasonCode esperado o None)
_TERMINAL_CASES = [
    ("S1_estandar_gold", Outcome.DRAFT_READY, None),
    ("S2_incompleto_sin_cantidad", Outcome.NEEDS_CLARIFICATION, ReasonCode.MISSING_QUANTITY),
    ("S5_sin_stock", Outcome.BLOCKED, ReasonCode.INSUFFICIENT_STOCK),
    ("S6_producto_desconocido", Outcome.BLOCKED, ReasonCode.UNKNOWN_SKU),
    ("S8_inyeccion_de_prompt", Outcome.REJECTED_BY_POLICY, ReasonCode.DISCOUNT_ABOVE_HARD_CEILING),
]


@pytest.mark.parametrize("prefix,expected_outcome,expected_reason", _TERMINAL_CASES)
async def test_scenario_reaches_expected_terminal_outcome(
    prefix: str, expected_outcome: Outcome, expected_reason: ReasonCode | None
) -> None:
    scenario = _scenario(prefix)
    result, _ = await _run(scenario)

    assert "__interrupt__" not in result, f"{prefix} no deberia requerir aprobacion humana"
    assert result["outcome"] == expected_outcome
    assert result["reason_code"] == expected_reason


# (prefijo del escenario, motivos de aprobacion esperados en la interrupcion)
_APPROVAL_CASES = [
    ("S3_aprobacion_por_monto", {ReasonCode.THRESHOLD_EXCEEDED}),
    ("S4_aprobacion_por_excepcion_descuento", {ReasonCode.DISCOUNT_EXCEPTION}),
    ("S7_cliente_desconocido", {ReasonCode.UNKNOWN_CUSTOMER}),
]


@pytest.mark.parametrize("prefix,expected_reasons", _APPROVAL_CASES)
async def test_scenario_pauses_for_approval_with_expected_reasons(
    prefix: str, expected_reasons: set[ReasonCode]
) -> None:
    scenario = _scenario(prefix)
    thread_id = f"test-{scenario['id']}-{uuid.uuid4()}"
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        state = QuoteState(
            thread_id=thread_id,
            customer_id=scenario["customer_id"],
            raw_text=scenario["raw_text"],
        )
        result = await graph.ainvoke(state, config=config)

        assert "__interrupt__" in result, f"{prefix} deberia pausar en human_approval"
        assert "outcome" not in result, f"{prefix} no deberia tener outcome antes de una decision"

        snapshot = await graph.aget_state(config)
        assert snapshot.next == ("human_approval",)

        actual_reasons = {r.reason_code for r in snapshot.values["approval_reasons"]}
        assert actual_reasons == expected_reasons


async def test_all_eight_scenarios_are_covered_exactly_once() -> None:
    """Guarda contra un desalineamiento silencioso entre este archivo y el
    seed: si alguien agrega un escenario a sample_requests.json sin agregar
    su caso aqui, esta prueba lo señala en vez de dejarlo sin cobertura."""
    covered_prefixes = {c[0] for c in _TERMINAL_CASES} | {c[0] for c in _APPROVAL_CASES}
    assert len(covered_prefixes) == 8
    for prefix in covered_prefixes:
        assert _scenario(prefix)  # lanza KeyError si el escenario no existe
