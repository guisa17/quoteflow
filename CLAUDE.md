# CLAUDE.md — Instrucciones persistentes del repositorio

Reglas obligatorias para cualquier asistente de código que trabaje en QuoteFlow.
Válido también como guía para una persona que retome el proyecto.

> Se eligió `CLAUDE.md` porque el desarrollo se hace con Claude Code, que **carga este archivo en contexto automáticamente en cada sesión**: así las reglas de abajo se aplican de verdad en lugar de quedar documentadas. `AGENTS.md` queda como puntero para otros runtimes.

---

## 1. Contexto en 30 segundos

QuoteFlow convierte una solicitud de cotización en texto libre en uno de **cinco resultados auditables**, mediante un grafo LangGraph con estado tipado, cálculo determinista y pausa real para decisión humana.

**Antes de tocar nada, leer en este orden:** [README.md](README.md) → [ROADMAP.md](docs/ROADMAP.md) (pendientes conocidos) → [REQUIREMENTS.md](docs/REQUIREMENTS.md) §2.
`ROADMAP.md` dice qué falta; `REQUIREMENTS.md` dice qué es correcto. La bitácora de construcción (fases, tareas T0–T14, evidencia) está en [docs/proceso/](docs/proceso/README.md) y es histórica.

## 2. Regla número uno: la frontera determinista

Definida en [ADR-002](docs/adr/ADR-002-frontera-determinista.md). **No se negocia sin un ADR nuevo.**

| Módulo | Puede | No puede |
|--------|-------|----------|
| `app/llm/` | Interpretar texto libre, redactar prosa | Leer política o inventario · decidir routing · producir cifras |
| `app/domain/` | Calcular, validar, decidir | Llamar a un LLM · hacer I/O de red |
| `app/graph/` | Orquestar, enrutar, interrumpir | Contener lógica de negocio propia |
| `app/api/` | Exponer y serializar | Contener reglas |

Verificación rápida: `app/domain/` **no importa nada de `app/llm/`**. Si esa línea se cruza, el cambio está mal.

## 3. Reglas de código no negociables

1. **`Decimal`, nunca `float`, en cualquier cálculo monetario** (BR-04). Redondeo `ROUND_HALF_UP` a 2 decimales.
2. **Ningún valor de dominio se codifica en el código.** Precios, stock, umbrales y máximos salen de `app/data/*.json` vía repositorios. Un número mágico en una regla es un bug.
3. **El texto del cliente jamás se concatena a las instrucciones del sistema** (BR-17). Se pasa como dato delimitado. Cualquier prompt nuevo respeta esto.
4. **La extracción se sanea antes de usarse** (ADR-002 §2): los campos de familias de dominio (precio, stock, nivel del cliente, aprobación) se descartan aunque el modelo los produzca. El nivel sale del padrón, no de "somos clientes Gold".
5. **Toda regla implementada cita su identificador** `BR-xx` / `RF-xx` en un comentario o en el nombre del test. Si una regla no existe en `REQUIREMENTS.md`, primero se escribe ahí.
6. **Sin secretos en el repo.** Toda variable nueva se agrega a `.env.example` con un valor de ejemplo inocuo.
7. **Toda decisión humana lleva `decision_id`** y es idempotente (BR-15). Un handler nuevo que no lo verifique está incompleto.

## 4. Ciclo de trabajo

`discutir → planificar → ejecutar → verificar → handoff`

1. **Planificar** — la tarea está descrita (en `docs/ROADMAP.md` → "Pendientes conocidos", o en la conversación) con archivos afectados, prueba asociada y criterio de terminado.
2. **Ejecutar** — **en una rama propia**, nunca directo en `main`; un cambio acotado por vez, con su prueba en el mismo paso.
3. **Verificar** — comandos abajo. **Un cambio sin prueba ejecutada no está hecho.**
4. **Handoff** — merge `--no-ff` a `main` solo con la suite en verde; actualizar `docs/ROADMAP.md` si cambia un pendiente y `docs/proceso/EVIDENCE.md` si hay una verificación nueva que registrar (comando + salida **real**).

### Commits y ramas

Se sigue [Conventional Commits 1.0](https://www.conventionalcommits.org/es/v1.0.0/), con la descripción en español:

```
tipo(ámbito): descripción en imperativo, minúscula, sin punto final

Cuerpo opcional: por qué se hace el cambio, no qué líneas cambian.
Refs: BR-18, ADR-005
```

| Tipo | Cuándo |
|------|--------|
| `feat` | Funcionalidad nueva para quien usa el sistema |
| `fix` | Corrige un comportamiento incorrecto |
| `docs` | Solo documentación (incluye ADR, README, ROADMAP) |
| `test` | Agrega o corrige pruebas, sin cambiar código de producción |
| `refactor` | Cambia la estructura sin cambiar el comportamiento |
| `style` | Formato o estilos visuales sin cambio de lógica |
| `perf` | Mejora de rendimiento |
| `build` | Dependencias, empaquetado, configuración de herramientas |
| `ci` | Workflows de GitHub Actions |
| `chore` | Mantenimiento que no encaja en lo anterior |

- **Ámbitos habituales:** `domain`, `graph`, `llm`, `api`, `ui`, `mocks`, `adr`, `evals`, `deps`.
- **Cambio incompatible:** `!` después del tipo (`feat(api)!: ...`) y un pie `BREAKING CHANGE: ...` que explique la migración.
- **Un commit, una intención.** Si la descripción necesita "y además", son dos commits.
- **Ramas:** `tipo/descripcion-corta`, por ejemplo `feat/evals-extractor` o `docs/adr-fase-4`. Se unen a `main` con `--no-ff` y el mensaje `Merge rama 'tipo/descripcion-corta'`.
- **Versiones:** [SemVer](https://semver.org/lang/es/) con tags anotados (`v0.5.0`). Antes de `v1.0.0`, `feat` sube la versión menor y `fix` la de parche.

El historial anterior a `v0.5.0` no sigue esta convención y no se reescribe: ya está publicado.

### Comandos de verificación

Son los mismos que corre el CI (`.github/workflows/ci.yml`) en cada push a `main` y en cada pull request.

**Si el cambio toca el prompt, el esquema del extractor o el modelo**, además hay que correr las evaluaciones contra el modelo real (`uv run python -m evals.run`, ver [backend/evals/](backend/evals/README.md)) y registrar el resultado en su tabla. No van en el CI porque gastan cuota.

```bash
cd backend
uv run pytest                                  # suite completa (LLM_MODE=fake)
uv run pytest tests/unit                       # reglas, sin Postgres
uv run ruff check . && uv run ruff format --check .
uv run mypy app/domain app/graph/state.py app/llm app/api app/config.py

cd ../frontend
pnpm typecheck && pnpm test && pnpm build
```

## 5. Honestidad de la evidencia

- En `EVIDENCE.md` va la **salida real** del comando, no la esperada. Si un test falla, se registra que falla.
- Lo no verificado se declara bajo "limitaciones", no se presenta como verificado.
- La deuda técnica se anota en `EVIDENCE.md` → "deuda aceptada", con su razón. Deuda documentada es una decisión; deuda silenciosa es un defecto.
- `AI_USE.md` registra herramientas, rol, outputs aceptados/rechazados y método de verificación. **Nunca razonamiento interno ni transcripciones.**

## 6. Gobierno

- **Un solo hilo de gobierno.** La cantidad de agentes no es el objetivo: sí lo son las tareas acotadas, el contexto persistente, el aislamiento cuando haya trabajo paralelo y la verificación independiente — el detalle de cómo se cumple cada uno está en [AI_USE.md](docs/proceso/AI_USE.md) §1. Si en algún momento se justifica trabajo paralelo, exige aislamiento por worktree y verificación independiente del resultado.
- **La documentación es fuente de verdad, no decoración.** Si el código y un documento discrepan, uno de los dos está mal y se corrige en el mismo ciclo — no en el siguiente.
- **Fuera de alcance es una decisión, no un olvido.** Antes de agregar una funcionalidad no listada, revisar `PROJECT.md` §2.3 (no alcance).

## 7. Riesgos técnicos conocidos

| Trampa | Qué hacer |
|--------|-----------|
| `AsyncPostgresSaver` necesita `await checkpointer.setup()` una vez antes del primer uso | Se hace en el `lifespan` de FastAPI, no por request |
| Un test de integración sin Postgres arriba falla de forma confusa | `docker compose up -d` y esperar `healthy`; `tests/unit` no lo necesita |
| Reanudar un grafo exige el mismo `thread_id` en el `config` | Persistir `thread_id` junto a la solicitud, nunca regenerarlo |
| `interrupt()` re-ejecuta el nodo desde el inicio al reanudar | Mantener los nodos idempotentes y sin efectos secundarios antes del `interrupt()` |
| El disponible es `on_hand − reserved`, no `on_hand` | Usar siempre el repositorio de inventario, nunca leer el JSON directo |
| En Windows, `psycopg` async falla con `InterfaceError` bajo `ProactorEventLoop`. En **pytest** (`tests/conftest.py`), fijar `asyncio.WindowsSelectorEventLoopPolicy()` a nivel de modulo basta. En **uvicorn** (>=0.36) **no** — `Server.run()` pasa un `loop_factory` explicito a `asyncio.run()` que ignora la politica por completo; el factory por defecto en Windows retorna `ProactorEventLoop` sin consultarla. Corregido y **verificado corriendo el servidor real** con `--loop app.main:loop_factory` (ver `app/main.py`, EVIDENCE.md). El primer intento de este fix (fijar la politica en `main.py`) parecia correcto por analogia con los tests y no lo era — se comprobó arrancando `uvicorn` de verdad, no solo corriendo la suite. No aplica en Linux/macOS (`SelectorEventLoop` ya es el único loop ahí, por eso el mismo factory funciona sin rama por plataforma) |
| Con la configuración por defecto de `psycopg_pool`, un backend encendido tardó 127 s en recuperarse de un reinicio real de Postgres | Ya resuelto en `app/db.py`: todo pool nuevo se crea con `create_pool` y se agrega a `maintain_pools`. No poner `asyncio.timeout` alrededor de operaciones del pool: usar su parámetro `timeout`. Un test que solo corta conexiones no reproduce esto: se comprueba reiniciando Postgres (EVIDENCE.md E-13) |
| Los tipos Pydantic propios en `QuoteState` (`Quote`, `Tier`, `AuditEvent`, etc.) no están registrados para el serializador msgpack del checkpointer; por defecto solo advierte, pero LangGraph anuncia que puede volverse estricto (`LANGGRAPH_STRICT_MSGPACK`) en una versión futura | Ya resuelto: `checkpointer_context()` construye un `JsonPlusSerializer(allowed_msgpack_modules=[...])` con los tipos de `QuoteState` explícitos. Si se agrega un campo con un tipo nuevo al estado, agregarlo también a `_QUOTE_STATE_TYPES` en `app/graph/checkpointer.py` |
