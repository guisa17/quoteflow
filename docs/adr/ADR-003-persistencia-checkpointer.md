# ADR-003 — Persistencia del flujo con `AsyncPostgresSaver`

- **Estado:** Aceptada
- **Fecha:** 2026-08-04
- **Afecta a:** `app/graph/checkpointer.py`, `app/graph/build.py`, `app/main.py`, pruebas de integración, `docker-compose.yml`

---

## Contexto

El requisito es explícito:

> El checkpointer es persistente. La memoria solo en proceso se admite en pruebas, no como solución final.

Y se convierte en criterio verificable:

> Reanudación durable: una ejecución interrumpida se recupera después de reiniciar.

Esto impone una condición sobre el flujo: cuando una solicitud queda en `PENDING_APPROVAL`, su estado debe sobrevivir a la caída del proceso que lo generó. La decisión humana puede llegar minutos u horas después, posiblemente contra otra instancia de la aplicación.

Hay además una restricción de contexto: el proyecto ya requiere Docker para nada más. Cualquier motor de persistencia adicional suma una dependencia de infraestructura que hay que justificar.

## Decisión

**Se usa `AsyncPostgresSaver` de `langgraph-checkpoint-postgres` sobre una única instancia de PostgreSQL**, levantada por `docker-compose.yml`.

Detalles operativos que se derivan:

1. **`setup()` se ejecuta una sola vez, en el arranque de la aplicación** (`lifespan` de FastAPI), nunca por request. Crea las tablas del checkpointer si no existen.
2. **El `thread_id` se persiste junto a la solicitud** y nunca se regenera. Es la única llave que permite reanudar; perderla equivale a perder el caso.
3. **La aplicación es asíncrona de extremo a extremo.** FastAPI y el grafo comparten el bucle de eventos, por lo que se usa la variante `Async` y no la síncrona.
4. **Postgres es también el almacén de la bandeja de solicitudes.** No se introduce un segundo motor para metadatos: una tabla propia junto a las del checkpointer.
5. **Las pruebas unitarias no requieren Postgres.** Los nodos y las reglas se prueban en aislamiento; solo `tests/integration/` levanta la base.

## Alternativas consideradas

| Alternativa | Descartada porque |
|-------------|-------------------|
| `MemorySaver` (memoria en proceso) | No sirve como solución final. Un reinicio perdería todas las solicitudes pendientes de aprobación, que es justo el caso que hay que demostrar |
| `SqliteSaver` | Persiste, y para un MVP local bastaría. Descartada por dos razones: el soporte asíncrono es menos directo que en la variante Postgres, y un archivo SQLite no representa el escenario multi-instancia que la fase de piloto haría inevitable. El costo de Postgres aquí es un contenedor |
| Postgres para el checkpointer + otro motor para metadatos | Complejidad sin retorno en un MVP: dos backends que mantener sincronizados para guardar media docena de campos |
| Serializar el estado a mano en una tabla propia | Reimplementa lo que el checkpointer ya resuelve —versionado de estado, reanudación desde `interrupt()`— con más superficie de error y sin ganancia |

## Consecuencias

**Positivas**

- La reanudación durable es demostrable de forma directa: la prueba de integración descarta la instancia del grafo, la reconstruye y reanuda con el mismo `thread_id`, replicando un reinicio real.
- El estado histórico de cada ejecución queda disponible para la auditoría (RF-08) sin construir un registro paralelo.
- Cambiar a una instancia gestionada de Postgres en un piloto no requiere tocar código: es una cadena de conexión.

**Negativas / límites asumidos**

- **Docker pasa a ser requisito para ejecutar la aplicación completa.** Se acota manteniendo `tests/unit` ejecutable sin base de datos, de modo que las reglas de negocio se pueden verificar en cualquier entorno.
- Un `setup()` mal ubicado (por request, o ausente) produce fallos confusos en el primer uso. Queda registrado como riesgo técnico conocido en [CLAUDE.md](../../CLAUDE.md) §7.
- Al reanudar, LangGraph re-ejecuta el nodo interrumpido desde su inicio. Los nodos deben ser inocuos antes del `interrupt()`; los efectos van después de `apply_decision`. Es también la base de la idempotencia exigida por BR-15.
- No se configura alta disponibilidad, replicación ni respaldos: infraestructura productiva está fuera de alcance por decisión ([PROJECT.md](../PROJECT.md) §2.3).
- **En Windows**, `psycopg` en modo asíncrono requiere `SelectorEventLoop`. En pruebas (`pytest`), fijar la política de `asyncio` a nivel de módulo (`tests/conftest.py`) basta. **En el servidor real no** — `uvicorn` >=0.36 pasa un `loop_factory` explícito a `asyncio.run()` que ignora la política del todo, y su factory por defecto en Windows construye `ProactorEventLoop` sin consultarla. El fix correcto es un `loop_factory` propio pasado a `uvicorn --loop` (`app/main.py`), verificado arrancando el servidor real, no solo la suite de tests — la analogía con el fix de `pytest` no se sostenía y hubiera quedado sin detectar de no probarse el proceso real. No afecta despliegues en Linux/macOS — registrado en [CLAUDE.md](../../CLAUDE.md) §7.

## Verificación

| Criterio | Prueba |
|----------|--------|
| El grafo interrumpe y persiste | `tests/integration/test_checkpointer.py` |
| Una ejecución se reanuda tras reiniciar | `tests/integration/test_interrupt_resume.py` (AC-09) |
| La misma decisión no duplica efectos | `tests/integration/test_idempotency.py` (AC-10) |
| Las reglas se verifican sin base de datos | `uv run pytest tests/unit` |
