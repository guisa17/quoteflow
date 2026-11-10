"""Checkpointer persistente (T11, ADR-003, RNF-01).

`AsyncPostgresSaver` sobre la unica instancia de Postgres del proyecto
(`docker-compose.yml`). `setup()` crea las tablas del checkpointer si no
existen -- debe correr una sola vez, en el arranque del proceso (el
`lifespan` de FastAPI en `app/main.py`, Fase 2 -- fuera del alcance de
T7-T11), nunca por request (CLAUDE.md §7, ADR-003 punto 1).

`checkpointer_context()` abre la conexion, corre `setup()` y entrega el
saver ya listo. Es lo que `app/main.py` reusara en su `lifespan` cuando se
construya la API (Fase 2), y lo que `tests/integration/` usa directamente
para probar interrupcion y reanudacion sin necesitar la API."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import Settings, get_settings
from app.db import create_pool
from app.domain.enums import DecisionAction, Outcome, ReasonCode, Tier
from app.domain.models import (
    ApprovalReason,
    Customer,
    ExtractedLineItem,
    Extraction,
    HumanDecision,
    Quote,
    ResolvedLine,
)
from app.graph.state import AuditEvent

# Tipos propios que aparecen en QuoteState (T7), registrados explicitamente
# para el serializador msgpack del checkpointer. Sin esto, LangGraph los trata
# como "no registrados": hoy solo advierte y deserializa igual, pero avisa que
# el comportamiento por defecto puede volverse estricto en una version futura
# (`LANGGRAPH_STRICT_MSGPACK`), momento en el que romperia en silencio la
# reanudacion de checkpoints existentes. Registrar aqui evita depender de ese
# comportamiento permisivo por defecto.
_QUOTE_STATE_TYPES = (
    Extraction,
    ExtractedLineItem,
    ResolvedLine,
    Quote,
    ApprovalReason,
    HumanDecision,
    Customer,
    Outcome,
    ReasonCode,
    Tier,
    DecisionAction,
    AuditEvent,
)


@asynccontextmanager
async def checkpointer_context(
    settings: Settings | None = None,
) -> AsyncIterator[AsyncPostgresSaver]:
    """Abre un pool hacia `settings.database_url`, corre `setup()` una vez y
    entrega el saver listo para usarse en `build_graph` (T11).

    Pool y no una conexion unica: un corte de Postgres no obliga a reiniciar el
    backend (`app/db.py`). `autocommit`, `prepare_threshold` y `row_factory` son
    los que exige `AsyncPostgresSaver`."""
    settings = settings or get_settings()
    serde = JsonPlusSerializer(allowed_msgpack_modules=_QUOTE_STATE_TYPES)
    async with create_pool(
        settings.database_url, autocommit=True, prepare_threshold=0, row_factory=dict_row
    ) as pool:
        # `row_factory=dict_row` hace que las filas sean dicts, pero mypy no
        # puede deducirlo de los kwargs: el cast solo declara lo que ya ocurre.
        dict_pool = cast("AsyncConnectionPool[AsyncConnection[DictRow]]", pool)
        checkpointer = AsyncPostgresSaver(conn=dict_pool, serde=serde)
        await checkpointer.setup()
        yield checkpointer
