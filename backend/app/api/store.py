"""Almacen de metadatos de solicitudes (bandeja) sobre Postgres (ADR-003).

La fuente de verdad del estado de ejecucion es el checkpointer de LangGraph
(app/graph/checkpointer.py). Esta tabla es un resumen denormalizado -- id,
cliente, outcome, motivo, resumen -- para que `GET /requests` no tenga que
reconstruir el estado completo de cada solicitud en cada listado (séria N
consultas al checkpointer por cada carga de la bandeja; deuda ya aceptada
en EVIDENCE.md D-02: sin paginacion, el volumen del MVP no la justifica,
y este resumen tampoco se pagina).

Se actualiza cada vez que la API avanza el grafo (crear o decidir), nunca
por el grafo mismo -- `app/graph/` no sabe que esta tabla existe.
"""

from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL,
    reason_code TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
)
"""


async def setup(conn: psycopg.AsyncConnection) -> None:
    """Crea la tabla si no existe. Se corre una sola vez, en el lifespan
    (CLAUDE.md §7: nunca por request)."""
    async with conn.cursor() as cur:
        await cur.execute(_CREATE_TABLE_SQL)
    await conn.commit()


async def insert(
    conn: psycopg.AsyncConnection,
    *,
    id_: str,
    thread_id: str,
    customer_id: str,
    customer_name: str,
    raw_text: str,
    summary: str,
    outcome: str,
    reason_code: str | None,
    now: datetime,
) -> None:
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO requests
                (id, thread_id, customer_id, customer_name, raw_text,
                 summary, outcome, reason_code, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_,
                thread_id,
                customer_id,
                customer_name,
                raw_text,
                summary,
                outcome,
                reason_code,
                now,
                now,
            ),
        )
    await conn.commit()


async def update_outcome(
    conn: psycopg.AsyncConnection,
    *,
    id_: str,
    customer_name: str,
    summary: str,
    outcome: str,
    reason_code: str | None,
    now: datetime,
) -> None:
    """No hace commit: se ejecuta dentro de la transaccion que retiene el
    bloqueo de `get_for_update`, y lo confirma quien abrio la conexion."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            UPDATE requests
            SET customer_name = %s, summary = %s, outcome = %s,
                reason_code = %s, updated_at = %s
            WHERE id = %s
            """,
            (customer_name, summary, outcome, reason_code, now, id_),
        )


async def get(conn: psycopg.AsyncConnection, id_: str) -> dict[str, Any] | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM requests WHERE id = %s", (id_,))
        return await cur.fetchone()


async def get_for_update(conn: psycopg.AsyncConnection, id_: str) -> dict[str, Any] | None:
    """Bloquea la fila hasta el fin de la transaccion: serializa las decisiones
    sobre una misma solicitud, tambien entre varios procesos (BR-19)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM requests WHERE id = %s FOR UPDATE", (id_,))
        return await cur.fetchone()


async def list_all(conn: psycopg.AsyncConnection) -> list[dict[str, Any]]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM requests ORDER BY updated_at DESC")
        return await cur.fetchall()
