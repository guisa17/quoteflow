"""Los 4 endpoints de RF-01..RF-04, contrato fijo en docs/API_CONTRACT.md.

Expone y serializa (CLAUDE.md §2): construye el `QuoteState` inicial, corre
o reanuda el grafo, traduce el resultado via `app/api/mapping.py`. Ninguna
regla de negocio vive aqui.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from langgraph.types import Command

from app.api import store
from app.api.mapping import (
    is_paused,
    resolve_outcome,
    resolve_reason_code,
    summarize,
    to_request_detail,
)
from app.api.schemas import CreateRequestBody, DecisionBody, RequestDetail, RequestSummary
from app.domain.decisions import DecisionVerdict, classify_decision
from app.domain.enums import Outcome
from app.graph.state import QuoteState

router = APIRouter(prefix="/requests", tags=["requests"])


def _config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _run_config(thread_id: str, run_name: str, **metadata: str) -> dict[str, Any]:
    """Config para ejecutar el grafo. `run_name` y `metadata` solo se usan si
    las trazas de LangSmith estan activas; `thread_id` agrupa en la vista de
    hilos el registro y la decision de una misma solicitud."""
    return {**_config(thread_id), "run_name": run_name, "metadata": metadata}


def _reason_for_cache(state: QuoteState, outcome: Outcome) -> str | None:
    code = resolve_reason_code(state, outcome)
    return code.value if code is not None else None


async def _current_state(request: Request, thread_id: str) -> tuple[QuoteState, bool]:
    graph = request.app.state.graph
    config = _config(thread_id)
    snapshot = await graph.aget_state(config)
    paused = is_paused(snapshot.next)
    state = QuoteState.model_validate({**snapshot.values, "thread_id": thread_id})
    return state, paused


async def _load_detail(request: Request, id_: str) -> RequestDetail:
    async with request.app.state.pool.connection() as conn:
        row = await store.get(conn, id_)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Solicitud '{id_}' no encontrada.")

    state, paused = await _current_state(request, row["thread_id"])
    return to_request_detail(
        id_=id_,
        state=state,
        customer_name=row["customer_name"],
        paused=paused,
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


@router.post("", status_code=201, response_model=RequestDetail)
async def create_request(body: CreateRequestBody, request: Request) -> RequestDetail:
    """RF-01: registra la solicitud y corre el grafo hasta un estado
    terminal o hasta `interrupt()`. Sincrona -- responde con `outcome` ya
    resuelto (nunca null; `PENDING_APPROVAL` cuenta como resuelto)."""
    id_ = str(uuid.uuid4())
    now = datetime.now(UTC)

    graph = request.app.state.graph
    initial_state = QuoteState(thread_id=id_, customer_id=body.customer_id, raw_text=body.raw_text)
    await graph.ainvoke(
        initial_state,
        config=_run_config(id_, "quoteflow.registro", customer_id=body.customer_id),
    )

    state, paused = await _current_state(request, id_)
    outcome = resolve_outcome(state, paused)
    customer_name = state.customer.legal_name if state.customer is not None else ""

    async with request.app.state.pool.connection() as conn:
        await store.insert(
            conn,
            id_=id_,
            thread_id=id_,
            customer_id=body.customer_id,
            customer_name=customer_name,
            raw_text=body.raw_text,
            summary=summarize(state),
            outcome=outcome.value,
            reason_code=_reason_for_cache(state, outcome),
            now=now,
        )

    return await _load_detail(request, id_)


@router.get("", response_model=list[RequestSummary])
async def list_requests(request: Request) -> list[RequestSummary]:
    """RF-02: bandeja. Lee solo la tabla de cache -- nunca reconstruye el
    estado completo de cada solicitud (ver store.py)."""
    async with request.app.state.pool.connection() as conn:
        rows = await store.list_all(conn)
    return [
        RequestSummary(
            id=r["id"],
            customer_id=r["customer_id"],
            customer_name=r["customer_name"],
            summary=r["summary"],
            outcome=Outcome(r["outcome"]),
            reason_code=r["reason_code"],
            updated_at=r["updated_at"].isoformat(),
        )
        for r in rows
    ]


@router.get("/{id_}", response_model=RequestDetail)
async def get_request(id_: str, request: Request) -> RequestDetail:
    """RF-03: detalle completo con trazabilidad."""
    return await _load_detail(request, id_)


@router.post("/{id_}/decision", response_model=RequestDetail)
async def decide_request(id_: str, body: DecisionBody, request: Request) -> RequestDetail:
    """RF-04: aprobar/rechazar/observar. Reenviar la misma decision devuelve
    200 sin efecto (BR-15); una decision que contradice lo registrado devuelve
    409 sin tocar el caso (BR-19). El bloqueo de la fila se mantiene hasta
    actualizar la bandeja, para que dos decisiones nunca se pisen."""
    graph = request.app.state.graph
    async with request.app.state.pool.connection() as conn:
        row = await store.get_for_update(conn, id_)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Solicitud '{id_}' no encontrada.")

        thread_id = row["thread_id"]
        state, paused = await _current_state(request, thread_id)
        verdict = classify_decision(
            decision_id=body.decision_id,
            action=body.action,
            paused=paused,
            applied_decision_ids=state.applied_decision_ids,
            last_decision=state.human_decision,
        )

        if verdict == DecisionVerdict.APPLY:
            decision_payload = {
                "decision_id": body.decision_id,
                "action": body.action.value,
                "actor": body.actor,
                "comment": body.comment,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await graph.ainvoke(
                Command(resume=decision_payload),
                config=_run_config(
                    thread_id,
                    "quoteflow.decision",
                    customer_id=row["customer_id"],
                    action=body.action.value,
                ),
            )
            state, paused = await _current_state(request, thread_id)

        outcome = resolve_outcome(state, paused)
        # Una caida entre reanudar el grafo y escribir aqui deja la bandeja
        # atrasada: cualquier decision posterior sobre el caso la repara.
        if verdict == DecisionVerdict.APPLY or row["outcome"] != outcome.value:
            await store.update_outcome(
                conn,
                id_=id_,
                customer_name=(
                    state.customer.legal_name
                    if state.customer is not None
                    else row["customer_name"]
                ),
                summary=summarize(state),
                outcome=outcome.value,
                reason_code=_reason_for_cache(state, outcome),
                now=datetime.now(UTC),
            )

    if verdict == DecisionVerdict.CONFLICT:
        raise HTTPException(
            status_code=409,
            detail=(
                "La decision contradice el estado actual de la solicitud y no se aplico. "
                "Recarga la solicitud para ver el resultado vigente."
            ),
        )

    return await _load_detail(request, id_)
