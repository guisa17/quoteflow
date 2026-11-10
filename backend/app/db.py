"""Pools de conexion a Postgres, con la misma resiliencia para ambos usos.

Medido contra un reinicio real de Postgres (EVIDENCE.md E-13): con la
configuracion por defecto de `psycopg_pool`, el backend tardaba 127 s en volver
a responder, porque la espera entre reintentos crece sin tope. Por eso:

- `maintain_pools` llama cada pocos segundos a `pool.check()`, la via publica de
  la libreria para descartar conexiones muertas y volver a intentar conectar.
- `reconnect_timeout` corto: un intento fallido se abandona pronto en vez de
  dormir cada vez mas, y el siguiente `check()` abre uno nuevo.
- `timeout` corto: con la base caida una peticion responde 503 enseguida (RNF-06)
  en vez de quedar colgada 30 s.
"""

import asyncio
import logging
from typing import Any

import psycopg
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

_ACQUIRE_TIMEOUT_SECONDS = 5.0
_RECONNECT_TIMEOUT_SECONDS = 5.0
_MAINTENANCE_INTERVAL_SECONDS = 2.0


def create_pool(database_url: str, **connection_kwargs: Any) -> AsyncConnectionPool:
    """Pool cerrado: se abre con `async with`. `connection_kwargs` se pasan a
    cada conexion nueva."""
    return AsyncConnectionPool(
        database_url,
        open=False,
        timeout=_ACQUIRE_TIMEOUT_SECONDS,
        reconnect_timeout=_RECONNECT_TIMEOUT_SECONDS,
        check=AsyncConnectionPool.check_connection,
        kwargs=connection_kwargs,
    )


async def maintain_pools(*pools: AsyncConnectionPool[Any]) -> None:
    """Corre hasta ser cancelada, durante toda la vida del proceso."""
    while True:
        await asyncio.sleep(_MAINTENANCE_INTERVAL_SECONDS)
        for pool in pools:
            try:
                await pool.check()
            except psycopg.Error as exc:
                logger.warning("No se pudo verificar el pool %s: %s", pool.name, exc)
