"""Configuracion compartida de pytest.

En Windows, asyncio usa ProactorEventLoop por defecto desde Python 3.8,
pero psycopg (usado por AsyncPostgresSaver, ADR-003) requiere
SelectorEventLoop para operar en modo asincrono -- ProactorEventLoop no
soporta las primitivas de socket que psycopg necesita. Sin este ajuste,
cualquier conexion async a Postgres falla con psycopg.InterfaceError en
Windows, aunque el mismo codigo funcione sin cambios en Linux/macOS.

Debe fijarse ANTES de que se cree el primer event loop -- por eso vive
aqui, a nivel de modulo (se ejecuta en la recoleccion de pytest, antes de
correr cualquier test), y no dentro de checkpointer.py: llamarlo desde
una corutina ya seria tarde, el loop ya existiria.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
