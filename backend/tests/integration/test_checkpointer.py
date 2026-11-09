"""T11 -- checkpointer persistente y compilacion del grafo (ADR-003, RF-07).

A diferencia de tests/unit, estas pruebas SI requieren Postgres arriba
(`docker compose up -d`, healthcheck en verde) -- CLAUDE.md §7: "un test de
integracion sin Postgres arriba falla de forma confusa". El DoD de T11 pide
exactamente lo que se verifica aqui: `AsyncPostgresSaver` con `setup()`, y
el grafo compilando e interrumpiendo en `human_approval`.

La reanudacion tras **reiniciar el proceso** (descartar la instancia del
grafo y reconstruirla) es AC-09 / T13, fuera del alcance de T7-T11. Aqui se
reanuda dentro del mismo proceso, sobre el mismo checkpointer persistente
-- ya demuestra que `interrupt()` + Postgres funcionan de punta a punta,
que es lo que T11 pide."""

import json
import uuid
from pathlib import Path

from langgraph.types import Command

from app.config import get_settings
from app.domain.enums import Outcome
from app.graph.build import build_graph
from app.graph.checkpointer import checkpointer_context
from app.graph.state import QuoteState

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"
_SAMPLE_REQUESTS = json.loads((_DATA_DIR / "sample_requests.json").read_text(encoding="utf-8"))


def _scenario(scenario_id_prefix: str) -> dict:
    for scenario in _SAMPLE_REQUESTS:
        if scenario["id"].startswith(scenario_id_prefix):
            return scenario
    raise KeyError(scenario_id_prefix)


def _initial_state(scenario_id_prefix: str, thread_id: str) -> QuoteState:
    scenario = _scenario(scenario_id_prefix)
    return QuoteState(
        thread_id=thread_id, customer_id=scenario["customer_id"], raw_text=scenario["raw_text"]
    )


async def test_setup_creates_checkpointer_tables_without_error() -> None:
    """ADR-003 punto 1: setup() crea las tablas del checkpointer si no
    existen. Llamarlo dos veces seguidas (dos context managers) no falla --
    es la forma en que cada test de este archivo lo invoca."""
    async with checkpointer_context() as checkpointer:
        assert checkpointer is not None
    async with checkpointer_context() as checkpointer:
        assert checkpointer is not None


async def test_graph_compiles_with_postgres_checkpointer() -> None:
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer, get_settings())
        assert graph is not None


async def test_graph_reaches_draft_ready_for_s1_without_interruption() -> None:
    """S1: dentro de politica -- no deberia pasar por human_approval en
    absoluto. Ejercita los 12 nodos y las 6 rutas condicionales de punta a
    punta contra Postgres real (AC-01..08 completo es T12, fuera de este
    alcance; esto es la prueba de humo de que el grafo compilado funciona)."""
    thread_id = f"test-s1-{uuid.uuid4()}"
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer, get_settings())
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke(_initial_state("S1", thread_id), config=config)

        assert "__interrupt__" not in result
        assert result["outcome"] == Outcome.DRAFT_READY
        assert result["quote"].total == result["quote"].net + result["quote"].tax_amount


async def test_graph_interrupts_at_human_approval_for_s3() -> None:
    """S3: neto 12900.00 > umbral 10000 -- el grafo debe pausar en
    human_approval (RF-07), no terminar solo."""
    thread_id = f"test-s3-{uuid.uuid4()}"
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer, get_settings())
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke(_initial_state("S3", thread_id), config=config)

        assert "__interrupt__" in result
        assert "outcome" not in result

        snapshot = await graph.aget_state(config)
        assert snapshot.next == ("human_approval",)


async def test_graph_resumes_after_approval_to_draft_ready() -> None:
    """Interrumpe (S3) y reanuda con el mismo thread_id sobre el mismo
    checkpointer -- confirma que Postgres persiste el estado necesario
    para que `Command(resume=...)` complete la ejecucion (ADR-003)."""
    thread_id = f"test-s3-resume-{uuid.uuid4()}"
    async with checkpointer_context() as checkpointer:
        graph = build_graph(checkpointer, get_settings())
        config = {"configurable": {"thread_id": thread_id}}

        paused = await graph.ainvoke(_initial_state("S3", thread_id), config=config)
        assert "__interrupt__" in paused

        decision_payload = {
            "decision_id": "dec-int-test-1",
            "action": "APPROVE",
            "actor": "jefe.ventas",
            "timestamp": "2026-08-04T00:00:00+00:00",
        }
        resumed = await graph.ainvoke(Command(resume=decision_payload), config=config)

        assert resumed["outcome"] == Outcome.DRAFT_READY
        assert resumed["draft"] is not None
        assert resumed["applied_decision_ids"] == ["dec-int-test-1"]
