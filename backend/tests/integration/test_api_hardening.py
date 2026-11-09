"""Regresiones de la API: stock acumulado (BR-13), cantidades no inventadas
(BR-01), decisiones (BR-15/BR-19), limites de entrada (BR-20), cache de la
bandeja y resiliencia de la conexion, contra Postgres real."""

import asyncio
from collections.abc import AsyncIterator

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app

_APPROVAL_TEXT = "Requerimos 60 arneses AR-450 para el proyecto de Arequipa."


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def _create(client: AsyncClient, raw_text: str, customer_id: str = "FER-1001") -> dict:
    response = await client.post(
        "/requests", json={"customer_id": customer_id, "raw_text": raw_text}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _decide(
    client: AsyncClient, request_id: str, decision_id: str, action: str, actor: str = "ana"
):
    return await client.post(
        f"/requests/{request_id}/decision",
        json={"decision_id": decision_id, "action": action, "actor": actor},
    )


async def test_br13_repeating_a_sku_cannot_bypass_the_stock_check(client: AsyncClient) -> None:
    """Hay 80 RP-300 disponibles: partir 81 en dos lineas sigue siendo 81."""
    body = await _create(client, "Necesito 80 RP-300 y ademas 1 unidad RP-300")
    assert body["outcome"] == "BLOCKED"
    assert body["blocking_reason"]["reason_code"] == "INSUFFICIENT_STOCK"
    assert "80" in body["blocking_reason"]["detail"]
    assert "81" in body["blocking_reason"]["detail"]
    assert body["quote"] is None


async def test_br01_a_previous_sku_never_supplies_a_quantity(client: AsyncClient) -> None:
    body = await _create(client, "Necesito 20 HX-200 y GL-500")
    assert body["outcome"] == "NEEDS_CLARIFICATION"
    assert body["blocking_reason"]["reason_code"] == "MISSING_QUANTITY"
    assert body["quote"] is None


async def test_br19_same_decision_id_with_another_action_does_not_approve(
    client: AsyncClient,
) -> None:
    created = await _create(client, _APPROVAL_TEXT)
    request_id = created["id"]

    observed = await _decide(client, request_id, "dec-conflict-1", "OBSERVE")
    assert observed.status_code == 200

    conflicting = await _decide(client, request_id, "dec-conflict-1", "APPROVE", actor="otro")
    assert conflicting.status_code == 409
    assert isinstance(conflicting.json()["detail"], str)

    detail = (await client.get(f"/requests/{request_id}")).json()
    assert detail["outcome"] == "PENDING_APPROVAL"
    assert detail["human_decision"]["action"] == "OBSERVE"
    assert detail["draft_text"] is None


async def test_br15_replaying_an_observation_adds_nothing_to_the_audit(
    client: AsyncClient,
) -> None:
    created = await _create(client, _APPROVAL_TEXT)
    request_id = created["id"]

    first = await _decide(client, request_id, "dec-observe-1", "OBSERVE")
    second = await _decide(client, request_id, "dec-observe-1", "OBSERVE")

    assert first.status_code == second.status_code == 200
    assert first.json()["audit_trail"] == second.json()["audit_trail"]


async def test_br19_contradicting_a_closed_case_is_reported_not_swallowed(
    client: AsyncClient,
) -> None:
    created = await _create(client, _APPROVAL_TEXT)
    request_id = created["id"]

    assert (await _decide(client, request_id, "dec-a", "APPROVE")).status_code == 200
    rejected = await _decide(client, request_id, "dec-b", "REJECT", actor="beto")
    assert rejected.status_code == 409

    detail = (await client.get(f"/requests/{request_id}")).json()
    assert detail["outcome"] == "DRAFT_READY"
    assert detail["human_decision"]["decision_id"] == "dec-a"


async def test_br19_decision_on_a_case_without_approval_is_a_conflict(client: AsyncClient) -> None:
    created = await _create(client, "Necesito 20 cascos HX-200 para Lima")
    assert created["outcome"] == "DRAFT_READY"

    response = await _decide(client, created["id"], "dec-a", "REJECT")
    assert response.status_code == 409


async def test_br19_concurrent_decisions_have_exactly_one_winner(client: AsyncClient) -> None:
    created = await _create(client, _APPROVAL_TEXT)
    request_id = created["id"]

    responses = await asyncio.gather(
        _decide(client, request_id, "dec-race-approve", "APPROVE", actor="ana"),
        _decide(client, request_id, "dec-race-reject", "REJECT", actor="beto"),
    )
    assert sorted(r.status_code for r in responses) == [200, 409]

    winner = next(r for r in responses if r.status_code == 200).json()
    detail = (await client.get(f"/requests/{request_id}")).json()
    assert detail["outcome"] == winner["outcome"]
    assert detail["human_decision"] == winner["human_decision"]
    applied = [e for e in detail["audit_trail"] if e["node"] == "apply_decision"]
    assert len(applied) == 1


async def test_replaying_a_decision_repairs_a_stale_inbox_row(client: AsyncClient) -> None:
    """Simula una caida entre reanudar el grafo y actualizar la bandeja."""
    created = await _create(client, _APPROVAL_TEXT)
    request_id = created["id"]
    assert (await _decide(client, request_id, "dec-heal", "APPROVE")).status_code == 200

    async with await psycopg.AsyncConnection.connect(
        get_settings().database_url, autocommit=True
    ) as conn:
        await conn.execute(
            "UPDATE requests SET outcome = 'PENDING_APPROVAL' WHERE id = %s", (request_id,)
        )

    assert (await _decide(client, request_id, "dec-heal", "APPROVE")).status_code == 200

    rows = (await client.get("/requests")).json()
    row = next(r for r in rows if r["id"] == request_id)
    assert row["outcome"] == "DRAFT_READY"


@pytest.mark.parametrize(
    "body",
    [
        {"customer_id": "", "raw_text": "Necesito 1 HX-200"},
        {"customer_id": "   ", "raw_text": "Necesito 1 HX-200"},
        {"customer_id": "FER-1001", "raw_text": "   "},
        {"customer_id": "FER-1001", "raw_text": "x" * 10_001},
        {"customer_id": "A" * 65, "raw_text": "Necesito 1 HX-200"},
    ],
)
async def test_br20_invalid_request_body_returns_422(client: AsyncClient, body: dict) -> None:
    response = await client.post("/requests", json=body)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"actor": ""},
        {"actor": "   "},
        {"actor": "a" * 255},
        {"decision_id": ""},
        {"decision_id": "d" * 129},
        {"comment": "c" * 2_001},
    ],
)
async def test_br20_invalid_decision_body_returns_422(client: AsyncClient, overrides: dict) -> None:
    created = await _create(client, _APPROVAL_TEXT)
    payload = {"decision_id": "dec-valid", "action": "APPROVE", "actor": "ana", **overrides}

    response = await client.post(f"/requests/{created['id']}/decision", json=payload)

    assert response.status_code == 422
    detail = (await client.get(f"/requests/{created['id']}")).json()
    assert detail["outcome"] == "PENDING_APPROVAL"


async def test_health_reports_ok_when_the_database_answers(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_reports_503_when_the_database_fails(client: AsyncClient) -> None:
    class _BrokenPool:
        def connection(self, *args, **kwargs):
            raise psycopg.OperationalError("base de datos caida")

    original = app.state.pool
    app.state.pool = _BrokenPool()
    try:
        response = await client.get("/health")
    finally:
        app.state.pool = original

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


async def test_rnf06_database_failure_returns_503_with_a_readable_message(
    client: AsyncClient,
) -> None:
    class _BrokenPool:
        def connection(self, *args, **kwargs):
            raise psycopg.OperationalError("detalle interno que no debe filtrarse")

    original = app.state.pool
    app.state.pool = _BrokenPool()
    try:
        response = await client.get("/requests")
    finally:
        app.state.pool = original

    assert response.status_code == 503
    assert "detalle interno" not in response.text
    assert isinstance(response.json()["detail"], str)


async def test_api_survives_lost_database_connections(client: AsyncClient) -> None:
    """Un corte de conexion no debe exigir reiniciar el backend: los pools
    verifican cada conexion antes de entregarla."""
    created = await _create(client, _APPROVAL_TEXT)

    async with await psycopg.AsyncConnection.connect(
        get_settings().database_url, autocommit=True
    ) as admin:
        await admin.execute(
            """
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity
            WHERE datname = current_database() AND pid <> pg_backend_pid()
            """
        )

    assert (await client.get(f"/requests/{created['id']}")).status_code == 200
    assert (await _decide(client, created["id"], "dec-after-cut", "APPROVE")).status_code == 200
