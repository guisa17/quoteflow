"""Punto de entrada de la API (Fase 2, RF-01..RF-04).

## Event loop en Windows -- corregido (ver CLAUDE.md §7 y ADR-003)

La primera version de este archivo asumia que fijar
`asyncio.set_event_loop_policy(...)` a nivel de modulo bastaba, igual que en
`tests/conftest.py`. Es **incorrecto** para `uvicorn` >=0.36: `Server.run()`
llama `asyncio_run(self.serve(...), loop_factory=self.config.get_loop_factory())`
-- un `loop_factory` explicito que construye el loop directamente, sin
consultar la politica de `asyncio` en absoluto. En Windows, el factory por
defecto ("asyncio") retorna `ProactorEventLoop` sin importar que politica
este fijada, asi que `psycopg` seguia fallando con el proceso real de
`uvicorn` aunque los tests (que no pasan por `Server.run()`) ya estuvieran
en verde. Verificado corriendo `uv run uvicorn app.main:app` de verdad
antes de esta correccion.

El fix real: `Config.get_loop_factory()` acepta una ruta de import propia
en `--loop`, no solo los nombres integrados ("auto"/"asyncio"/"uvloop").
`loop_factory` de abajo se expone para eso -- ver README para el comando
exacto. Funciona igual en Linux/macOS (`SelectorEventLoop` ya es el unico
loop que usan), asi que no hace falta una rama por plataforma.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import psycopg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg_pool import AsyncConnectionPool

from app.api import store
from app.api.routes import router
from app.config import configure_tracing, get_settings
from app.db import create_pool, maintain_pools
from app.graph.build import build_graph
from app.graph.checkpointer import checkpointer_context

# El logger de uvicorn ya esta configurado: sus mensajes INFO se ven en consola.
logger = logging.getLogger("uvicorn.error")

_HEALTH_ACQUIRE_TIMEOUT_SECONDS = 2.0


def loop_factory() -> asyncio.AbstractEventLoop:
    """Para `uvicorn --loop app.main:loop_factory` (ver README). psycopg
    async requiere `SelectorEventLoop`; el `ProactorEventLoop` que uvicorn
    usaria por defecto en Windows lo rompe con `InterfaceError`."""
    return asyncio.SelectorEventLoop()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Corre una sola vez, al arrancar el proceso (CLAUDE.md §7, ADR-003):
    abre el checkpointer (setup() de sus tablas), compila el grafo, abre el
    pool de conexiones para la tabla `requests` (store.py) y crea esa tabla
    si no existe. Todo queda en `app.state` para que las rutas lo reusen sin
    reabrir nada por request."""
    settings = get_settings()
    if configure_tracing(settings):
        logger.info("Trazas de LangSmith activas (proyecto %s).", settings.langsmith_project)
    async with checkpointer_context(settings) as checkpointer:
        graph = build_graph(checkpointer, settings)

        async with create_pool(settings.database_url) as pool:
            async with pool.connection() as conn:
                await store.setup(conn)

            app.state.graph = graph
            app.state.pool = pool
            # `checkpointer_context` siempre construye el saver sobre un pool;
            # el tipo de `conn` admite tambien una conexion suelta.
            checkpointer_pool = checkpointer.conn
            assert isinstance(checkpointer_pool, AsyncConnectionPool)
            app.state.checkpointer_pool = checkpointer_pool

            maintenance = asyncio.create_task(maintain_pools(pool, checkpointer_pool))
            try:
                yield
            finally:
                maintenance.cancel()
                with suppress(asyncio.CancelledError):
                    await maintenance


app = FastAPI(title="QuoteFlow API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(psycopg.OperationalError)
async def database_unavailable(_request: Request, _exc: psycopg.OperationalError) -> JSONResponse:
    """RNF-06: base de datos no disponible, con mensaje accionable y sin traza."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": "La base de datos no está disponible. Intenta de nuevo en unos segundos."
        },
    )


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    """200 solo si responden los dos pools hacia Postgres que usa la API: el de
    la tabla `requests` y el del checkpointer. 503 en cualquier otro caso."""
    try:
        for pool in (request.app.state.pool, request.app.state.checkpointer_pool):
            async with pool.connection(timeout=_HEALTH_ACQUIRE_TIMEOUT_SECONDS) as conn:
                await conn.execute("SELECT 1")
    except psycopg.OperationalError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(content={"status": "ok"})
