# EVIDENCE — Comandos ejecutados, resultados y limitaciones

Registro de verificación. Contiene **la salida real** de cada comando, no la esperada. Si algo falla, se registra que falla.

**Última actualización:** 2026-11-09 · **Fase cubierta:** 0 (encuadre y especificación) + **Fase 1 completa (T0-T14)** + **Fase 2 completa** (`app/api/` + frontend) + correcciones de E-13

> **Estado de esta fase:** dominio (T2-T6), grafo completo (T7-T11) y cobertura sistemática (T12-T14) hechos y verificados: 139 tests, sin LLM externo. Frontend (RF-09) construido y verificado de forma independiente (E-10). `app/api/` (RF-01…RF-04) construido, probado y **arrancado como servidor real** contra Postgres real (E-11) — no solo verificado por tests. Las secciones E-01 a E-03 cubren la Fase 0; E-04/E-05 T0-T1; E-06/E-07 dominio y Postgres; E-08 T7-T11; E-09 T12-T14; E-10 frontend; E-11 `app/api/`.

---

## E-01 · Cobertura de la especificación

**Objetivo:** confirmar que `PROJECT.md` y `REQUIREMENTS.md` cubren íntegramente los requisitos del producto, sin omitir ni reinterpretar ninguno.

**Método:** contraste punto por punto de la especificación escrita contra los requisitos iniciales.

**Resultado:** ✅ aparecen íntegros los 5 resultados del sistema, las 7 reglas de negocio mínimas, los 7 requisitos técnicos, los 7 criterios del Definition of Done, los 5 puntos de la interfaz mínima y el caso de referencia.

---

## E-02 · Validez del seed y aritmética de los escenarios

**Objetivo:** confirmar que los 8 escenarios alcanzan su `expected_outcome` **antes** de escribir el código que debe reproducirlos.

**Comando:** script de recálculo sobre `backend/app/data/*.json`, aplicando `subtotal = qty × precio`, `descuento = subtotal × pct/100`, `neto = subtotal − descuento`, `IGV = neto × 0.18`.

**Salida real:**

```
JSON OK -- productos=6 clientes=3 escenarios=8
Disponible: AR-450=80  BT-900=140  GL-500=1200  HX-200=350  LN-120=2000  RP-300=80
Techo duro=20.0%  Umbral=10000.00  IGV=0.18
GOLD=12.0% SILVER=8.0% STANDARD=5.0%

S1  HX-200 x20   tier=GOLD (max 12.0%) pedido=8%   disp=350   sub=900.00    desc=72.00  NETO=828.00    igv=149.04  total=977.04
S3  AR-450 x60   tier=GOLD (max 12.0%) pedido=0%   disp=80    sub=12900.00  desc=0.00   NETO=12900.00  igv=2322.00 total=15222.00
S4  BT-900 x40   tier=STANDARD (max 5.0%) pedido=10%  disp=140  sub=3560.00 desc=356.00 NETO=3204.00   igv=576.72  total=3780.72
S5  RP-300 x300  tier=SILVER (max 8.0%) pedido=0%  disp=80    sub=18600.00  desc=0.00   NETO=18600.00  igv=3348.00 total=21948.00
S7  LN-120 x100  tier=STANDARD(desconocido) (max 5.0%) pedido=0%  disp=2000  sub=1275.00  desc=0.00  NETO=1275.00  igv=229.50  total=1504.50
S8  LN-120 x50   tier=SILVER (max 8.0%) pedido=40%  disp=2000  sub=637.50   desc=255.00 NETO=382.50    igv=68.85   total=451.35
```

**Interpretación:**

| Escenario | Comprobación | Resultado |
|-----------|--------------|-----------|
| `S1` | 8 % ≤ 12 % (GOLD) y neto 828.00 < 10 000 ⇒ `DRAFT_READY` | ✅ |
| `S3` | Neto 12 900.00 > 10 000 y disponible 80 ≥ 60 ⇒ `PENDING_APPROVAL` / `THRESHOLD_EXCEEDED` | ✅ |
| `S4` | 10 % > 5 % (STANDARD) y neto 3 204.00 < 10 000 ⇒ único motivo `DISCOUNT_EXCEPTION` | ✅ |
| `S5` | Disponible 80 < 300 solicitados ⇒ `BLOCKED` antes de cotizar | ✅ |
| `S7` | Cliente ausente del padrón y neto 1 275.00 < 10 000 ⇒ único motivo `UNKNOWN_CUSTOMER` | ✅ |
| `S8` | 40 % > techo duro 20 % ⇒ `REJECTED_BY_POLICY`, nunca aprobación | ✅ |

**Propiedad relevante del seed:** cada escenario aísla **exactamente un motivo**. `S4` y `S7` quedan holgadamente bajo el umbral de monto, de modo que si un test falla, el motivo es inequívoco.

`S2` (falta cantidad) y `S6` (SKU inexistente) no aparecen en la tabla porque se resuelven **antes** de cualquier cálculo: no hay aritmética que verificar.

---

## E-03 · Integridad de la documentación

**Objetivo:** que ningún documento prometa un archivo que no existe.

**Comando:** recorrido de los enlaces Markdown relativos de todos los `.md` del repositorio, comprobando la existencia del destino.

**Salida real:**

```
Enlaces internos revisados: 162  |  rotos: 0
Documentos .md en el repo: 17
```

✅ Los documentos que aún no existen se referencian como texto con marca 🚧, nunca como enlace.

---

## E-04 · T0 — Inicialización de Git y primer commit

**Comando:**

```bash
git init -q -b main
git add -A
git commit -m "Fase 0: encuadre, especificacion y andamiaje del proyecto"
```

**Salida real:**

```
3c4da49 Fase 0: encuadre, especificacion y andamiaje del proyecto
```

`git status --short` tras el commit: sin salida (árbol limpio). 26 archivos versionados, ninguno de ellos `.env`, credenciales, ni `_local/`.

**Remoto:** repositorio privado creado en `https://github.com/guisa17/quoteflow` vía `gh repo create --private --source=. --remote=origin --push`.

---

## E-05 · T1 — Bootstrap del backend

**Comando:**

```bash
cd backend
uv sync
```

**Salida real (resumen):** `Using CPython 3.12.13` · `Resolved 63 packages` · `Installed 62 packages` — incluye `fastapi`, `langgraph`, `langgraph-checkpoint-postgres`, `psycopg[binary,pool]`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`.

**Verificación — import e I/O de configuración:**

```bash
uv run python -c "import app; from app.config import get_settings; s = get_settings(); print(s.llm_mode, s.database_url, s.cors_origin_list)"
```

```
OK import app
llm_mode = fake
database_url = postgresql://quoteflow:quoteflow@localhost:5432/quoteflow
cors_origin_list = ['http://localhost:5173']
```

`Settings` lee `.env` (copiado desde `.env.example`) y expone valores tipados; `llm_mode` por defecto es `fake`, el modo seguro sin dependencia de red.

**Verificación — herramientas de calidad:**

```bash
uv run ruff check .
```
```
All checks passed!
```

```bash
uv run mypy app/domain
```
```
Success: no issues found in 1 source file
```

`mypy app/graph/state.py` falla con *"No such file or directory"* — correcto y esperado: ese archivo es de T7, todavía no existe. No es un error de configuración; confirma que `mypy` apunta al archivo correcto en cuanto exista.

**Resultado:** ✅ T1 completo. `app/domain/`, `app/graph/`, `app/llm/`, `app/api/` existen como paquetes vacíos, listos para T2-T9.

---

## E-06 · T2-T6 — Dominio determinista completo

**Objetivo:** que precios, política, validación y acceso a datos existan como funciones deterministas puras, probadas sin LLM ni Postgres, antes de tocar LangGraph (regla de orden de `PHASE_01.md`).

| Tarea | Módulo | Qué verifica cada test | Tests |
|---|---|---|---|
| T2 | `app/domain/{enums,models}.py` | Los 4 enums del dominio; `Decimal` (no `float`) al parsear precios desde JSON; la extracción descarta campos fuera de esquema (BR-03/ADR-002 §2); `ROUND_HALF_UP` explícito | 11/11 |
| T3 | `app/domain/repositories.py` | Los 4 repositorios cargan el seed real; SKU/cliente desconocido → `None`; normalización BR-02 sin sustitución por similitud | 8/8 |
| T4 | `app/domain/pricing.py` | AC-01 reproducido al centavo; S3 y S4 del seed; suma de líneas multi-item; redondeo en un caso límite (`1.005 → 1.01`) | 6/6 |
| T5 | `app/domain/policy.py` | S1, S3, S4, S7, S8 del seed; **BR-09**: el rechazo por techo duro domina sobre motivos de aprobación concurrentes; motivos que sí concurren se acumulan en una sola decisión; límites exactos (`>` estricto, no `>=`) en las tres reglas | 10/10 |
| T6 | `app/domain/validation.py` | S2 (cantidad faltante), S5 (stock insuficiente, reporta disponible real), S6 (SKU inexistente); BR-11 (sede/fecha ausentes no bloquean); BR-12 (fallo en el segundo ítem descarta líneas ya resueltas del primero) | 8/8 |

**Comando y salida real:**

```bash
cd backend
uv run pytest tests/unit -q
```
```
tests\unit\test_models.py ...........                                    [ 25%]
tests\unit\test_policy.py ..........                                     [ 48%]
tests\unit\test_pricing.py ......                                        [ 62%]
tests\unit\test_repositories.py ........                                 [ 81%]
tests\unit\test_validation.py ........                                   [100%]

============================= 43 passed in 0.19s ==============================
```

```bash
uv run ruff check . && uv run ruff format --check .
```
```
All checks passed!
17 files already formatted
```

```bash
uv run mypy app/domain
```
```
Success: no issues found in 7 source files
```

**Decisión de diseño registrada durante T3:** BR-02 dice "sin espacios... sobrantes". La primera implementación solo colapsaba espacios repetidos, y un test con espacios alrededor de un guion (`"HX - 200"`) falló porque quedaba un espacio simple sin eliminar. Se corrigió la función (elimina todo espacio interno, no solo los repetidos) en vez de relajar el test — un SKU no tiene espacios legítimos, así que cualquier espacio es "sobrante" por definición. El test que expuso el caso se mantiene tal cual.

**Resultado:** ✅ T2-T6 completos. El dominio determinista existe y está probado independientemente del grafo, del LLM y de Postgres.

---

## E-07 · Verificación de Postgres

**Objetivo:** de-riesgar T11 (`AsyncPostgresSaver`) antes de tiempo, verificando que `docker-compose.yml` y `DATABASE_URL` funcionan de extremo a extremo.

```bash
docker compose up -d
docker compose ps
```
```
NAME                 STATUS
quoteflow-postgres   Up 28 seconds (healthy)
```

```bash
uv run python -c "
import psycopg
from app.config import get_settings
s = get_settings()
with psycopg.connect(s.database_url, connect_timeout=5) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT version();')
        print('Conectado OK ->', cur.fetchone()[0][:60])
"
```
```
Conectado OK -> PostgreSQL 16.14 on x86_64-pc-linux-musl, compiled by gcc (A
```

**Resultado:** ✅ Cadena completa verificada: healthcheck de Docker → `.env` → `Settings` → `psycopg`. `AsyncPostgresSaver` en T11 no debería enfrentar sorpresas de conectividad.

---

## E-08 · T7-T11 — Grafo completo, checkpointer y persistencia real

**Método de trabajo:** T7-T10 (estado tipado, extractor determinista, 12 nodos, routing) se delegaron a una sesión nueva de Claude Code (Sonnet), briefeada únicamente con `CLAUDE.md`, `STATE.md`, `PHASE_01.md`, `REQUIREMENTS.md` y `PROJECT.md` §4 — sin nada heredado de la sesión que construyó el dominio. Es la prueba real de si esos documentos bastan para continuar el trabajo sin contexto de conversación. Detalle del criterio en `AI_USE.md` §1.

**Incidente registrado durante T11:** a mitad de los tests de integración contra Postgres, Docker Desktop entró en una falla real del motor (confirmado con `docker info` colgándose por timeout, no un diagnóstico erróneo del agente). La causa raíz, identificada después: el backend de Docker Desktop reportaba 0 CPUs disponibles a su propia VM — un `wsl --shutdown` no lo resolvió; un reinicio completo del sistema sí. Ningún archivo se perdió: los que ya estaban escritos en disco (`build.py`, `checkpointer.py`, `tests/integration/`) sobrevivieron intactos al reinicio, sin comitear, exactamente como se dejaron.

**Comando y salida real, tras el reinicio:**

```bash
docker compose up -d && docker compose ps
```
```
quoteflow-postgres   Up 3 seconds (healthy)
```

**Primer intento — falló por un problema real, no ambiental:**

```bash
uv run pytest tests/integration/test_checkpointer.py -v
```
```
psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in
async mode. Please use a compatible event loop...
5 failed in 2.64s
```

**Diagnóstico:** en Windows, `asyncio` usa `ProactorEventLoop` por defecto desde Python 3.8; `psycopg` en modo async requiere `SelectorEventLoop`. Es un problema específico de Windows — el mismo código funciona sin cambios en Linux/macOS, así que no es un riesgo de despliegue. Fix: `tests/conftest.py` fija `asyncio.WindowsSelectorEventLoopPolicy()` antes de que exista el primer event loop. Registrado como riesgo técnico conocido en `CLAUDE.md` §7 y como límite operativo en `ADR-003`.

**Segundo intento, con el fix:**

```bash
uv run pytest tests/integration/test_checkpointer.py -v
```
```
test_setup_creates_checkpointer_tables_without_error PASSED
test_graph_compiles_with_postgres_checkpointer PASSED
test_graph_reaches_draft_ready_for_s1_without_interruption PASSED
test_graph_interrupts_at_human_approval_for_s3 PASSED
test_graph_resumes_after_approval_to_draft_ready PASSED
5 passed in 5.12s
```

**Suite completa y calidad:**

```bash
uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy app/domain app/graph/state.py
```
```
116 passed in 4.87s
All checks passed!
32 files already formatted
Success: no issues found in 9 source files
```

**Interpretación:** 116 tests (111 unitarios + 5 de integración). El grafo de 12 nodos compila, S1 corre de punta a punta hasta `DRAFT_READY` sin pasar por `human_approval`, S3 se interrumpe correctamente en `human_approval` (RF-07), y `Command(resume=...)` completa la ejecución hasta `DRAFT_READY` reutilizando el mismo `thread_id` sobre Postgres real.

**Límite de esta evidencia:** la reanudación aquí ocurre dentro del mismo proceso — se prueba que `interrupt()` + Postgres persisten lo necesario, pero no que sobreviva a la caída y reconstrucción real del proceso. Eso es específicamente T13, con su propia evidencia.

**Resultado:** ✅ T7-T11 completos.

---

## E-09 · T12-T14 — Cobertura sistemática: escenarios, reinicio real, idempotencia

**Hallazgo encontrado y corregido antes de escribir estas pruebas:** el nodo `finalize` (T9) marcaba con un comentario una ambigüedad sin resolver — `REQUIREMENTS.md` AC-11 decía literalmente "`REJECT` ⇒ `REJECTED`", pero el enum `Outcome` (T2, contrato fijo) no tiene un valor `REJECTED` separado, solo `REJECTED_BY_POLICY`. El código y un test unitario ya construido por la sesión de Sonnet (`test_finalize_human_reject_maps_to_rejected_by_policy`) ya asumían la interpretación correcta: "rechazado o escalado por política" es un solo resultado. Se corrigió `REQUIREMENTS.md` para que dijera lo mismo que el código, en vez de ajustar el código a una redacción imprecisa de la especificación original.

**Segundo hallazgo, con fix aplicado:** al ejecutar el grafo por primera vez tras el reinicio, LangGraph advirtió que los tipos Pydantic propios (`Quote`, `Tier`, `AuditEvent`, etc.) no estaban registrados para su serializador msgpack, y que la deserialización de tipos no registrados **se bloqueará en una versión futura**. Se resolvió construyendo un `JsonPlusSerializer(allowed_msgpack_modules=[...])` explícito en `checkpointer_context()` con los tipos reales de `QuoteState` — no strings, clases importadas, para que un renombre falle en el import en vez de en silencio. Verificado: la advertencia desaparece, el comportamiento no cambia.

**T12 — los 8 escenarios completos:**

```bash
uv run pytest tests/integration/test_scenarios.py -v
```
```
test_scenario_reaches_expected_terminal_outcome[S1...DRAFT_READY-None] PASSED
test_scenario_reaches_expected_terminal_outcome[S2...NEEDS_CLARIFICATION-MISSING_QUANTITY] PASSED
test_scenario_reaches_expected_terminal_outcome[S5...BLOCKED-INSUFFICIENT_STOCK] PASSED
test_scenario_reaches_expected_terminal_outcome[S6...BLOCKED-UNKNOWN_SKU] PASSED
test_scenario_reaches_expected_terminal_outcome[S8...REJECTED_BY_POLICY-DISCOUNT_ABOVE_HARD_CEILING] PASSED
test_scenario_pauses_for_approval_with_expected_reasons[S3...] PASSED
test_scenario_pauses_for_approval_with_expected_reasons[S4...] PASSED
test_scenario_pauses_for_approval_with_expected_reasons[S7...] PASSED
test_all_eight_scenarios_are_covered_exactly_once PASSED
9 passed in 8.85s
```

**T13 — reanudación tras un reinicio real del proceso (no solo del mismo objeto de grafo):**

```bash
uv run pytest tests/integration/test_interrupt_resume.py -v
```
```
test_resumes_to_draft_ready_after_discarding_and_rebuilding_the_graph PASSED
test_resumed_execution_preserves_full_audit_trail_across_the_restart PASSED
2 passed in 4.10s
```

Diferencia deliberada con T11: ese test reanuda sobre la misma instancia de grafo dentro del mismo `async with`. Aquí el bloque se cierra por completo, `graph` y `checkpointer` se descartan (`del`), y se reconstruyen desde cero antes de reanudar — la única forma de probar que lo necesario para reanudar vive en Postgres, no en memoria de Python.

**T14 — idempotencia y rechazo humano:**

```bash
uv run pytest tests/integration/test_idempotency.py -v
```
```
test_ac10_resubmitting_the_same_decision_id_produces_no_additional_effect PASSED
test_ac10_resubmission_returns_the_same_state_not_a_divergent_one PASSED
test_ac11_human_rejection_reaches_rejected_by_policy_with_audit PASSED
3 passed in 5.88s
```

**Nota de método sobre AC-10:** BR-15 solo es observable si el grafo sigue pausado después de aplicar una decisión — por eso se ejercita reenviando el mismo `decision_id` con acción `OBSERVE` (que mantiene el caso en pausa, BR-14), no `APPROVE` (que resuelve el caso y no deja nada que reenviar). Un primer intento de este test usó `snapshot.values["outcome"]` asumiendo que la clave siempre existe; falló con `KeyError` porque LangGraph omite del dict las claves que ningún nodo ha escrito todavía — mismo comportamiento que en `result` al interrumpir. Corregido a `"outcome" not in snapshot.values`.

**Suite completa, verificación final:**

```bash
uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy app/domain app/graph/state.py
```
```
130 passed in 20.74s
All checks passed!
35 files already formatted
Success: no issues found in 9 source files
```

**Resultado:** ✅ T12-T14 completos. Fase 1 (dominio + grafo + persistencia + integración sistemática) cerrada: 130 tests, sin depender de un LLM externo ni de un modelo real, cumpliendo RF-10.

---

## E-10 · Frontend (RF-09) — verificación independiente

**Método:** el frontend se construyó en una sesión delegada de Sonnet (50 archivos, sin tocar nada fuera de `frontend/` — confirmado con `git show --stat` filtrado). Lo que sigue es la verificación de la sesión principal sobre ese resultado, no una transcripción de su propio reporte.

**Aislamiento confirmado:**
```bash
git show --stat 58b279b | grep -v "^frontend/"
```
Ningún archivo fuera de `frontend/` en el diff. `git status` limpio antes y después.

**Hallazgo 1 — gestor de paquetes.** El brief original decía `npm install`; el usuario señaló la inconsistencia con el resto de sus proyectos (`pnpm`). Conversión aplicada tras el cierre del agente (sin colisión, ya no escribía en `frontend/`):
```bash
rm -rf node_modules package-lock.json && pnpm install && pnpm approve-builds esbuild
```
`pnpm-lock.yaml` y `pnpm-workspace.yaml` (con la aprobación del postinstall de `esbuild`) generados y comiteados. `package.json` con `"packageManager": "pnpm@11.1.3"`.

**Hallazgo 2 — la verificación de los 8 escenarios no era reproducible.** El reporte del agente afirmaba que `src/mocks/engine.ts` reproduce AC-01…AC-08, pero lo verificó con "un script ad-hoc, no quedó como suite Vitest" (cita literal de su propio reporte). Se agregó `vitest` y `src/mocks/engine.test.ts` — 8 escenarios + 2 casos de reanudación (`APPROVE`/`REJECT`) — como test real, no como confirmación de segunda mano:
```bash
pnpm add -D vitest
pnpm run test
```
```
Test Files  1 passed (1)
     Tests  11 passed (11)
```

**Hallazgo 3 — advisory de seguridad, verificado en vez de solo repetido.** El reporte descartaba un hallazgo de `npm audit` (CSRF en modo RSC de `react-router`, GHSA-qwww-vcr4-c8h2) por no aplicar a un SPA. Se confirmó de forma independiente:
```bash
pnpm audit
grep -rn "react-router\|RouterProvider\|rsc" src/
```
El proyecto usa `createBrowserRouter`/`RouterProvider` (modo *data router* del lado del cliente); cero imports de `react-router/rsc` o Server Components en `src/`. La evaluación del reporte era correcta — se documenta en `frontend/README.md` como riesgo evaluado y descartado, sin forzar el salto a `react-router` v8 (breaking) sin tiempo de regresión.

**Re-verificación completa tras las correcciones:**
```bash
pnpm run typecheck && pnpm run test && pnpm run build
```
```
$ tsc -b --noEmit
(sin salida — limpio)
Test Files  1 passed (1)
     Tests  11 passed (11)
✓ built in 9.34s
```

**Resultado:** ✅ Frontend verificado de forma independiente. `typecheck` limpio, 11/11 tests reales (no ad-hoc), `build` sin errores, gestor de paquetes corregido, advisory de seguridad confirmado como no aplicable. Pendiente: `app/api/` real para probar `src/api/client.ts` contra un servidor de verdad (ver `STATE.md`).

---

## E-11 · `app/api/` (RF-01…RF-04) — construido, probado, y verificado como servidor real

**Diseño:** 4 endpoints (`schemas.py`, `store.py`, `mapping.py`, `routes.py`) contra el contrato fijo de `docs/API_CONTRACT.md`. `store.py` mantiene una tabla `requests` como resumen denormalizado de la bandeja (decisión ya comprometida en ADR-003: "una tabla propia junto a las del checkpointer") — evita reconstruir el estado completo de cada solicitud en cada `GET /requests`.

**Tests de integración (`tests/integration/test_api.py`), vía `httpx.AsyncClient` + `app.router.lifespan_context` (lifespan real, sin mockear nada):**

```bash
uv run pytest tests/integration/test_api.py -v
```
```
test_s1_create_request_reaches_draft_ready_synchronously PASSED
test_s2_missing_quantity_reaches_needs_clarification PASSED
test_s3_pending_approval_then_approve_via_decision_endpoint PASSED
test_ac10_resending_the_same_decision_id_is_idempotent PASSED
test_s8_prompt_injection_rejected_never_approved PASSED
test_get_unknown_request_returns_404 PASSED
test_decision_on_unknown_request_returns_404 PASSED
test_decision_with_invalid_action_returns_422 PASSED
test_list_requests_reflects_created_requests PASSED
9 passed in 14.43s
```

**Hallazgo real — el fix de Windows de T11 estaba incompleto.** Antes de aceptar la API como terminada, se arrancó el servidor real (`uv run uvicorn app.main:app`), no solo la suite. Falló:

```
psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in
async mode...
ERROR: Application startup failed. Exiting.
```

El fix de T11 (`asyncio.set_event_loop_policy(...)` a nivel de módulo) funciona en `pytest` porque pytest-asyncio crea sus loops respetando la política vigente. **No funciona con `uvicorn` >=0.36**: `Server.run()` llama `asyncio_run(self.serve(...), loop_factory=self.config.get_loop_factory())` — un `loop_factory` explícito que construye el loop directamente, sin consultar la política. En Windows, el factory por defecto de `uvicorn` retorna `ProactorEventLoop` sin importar qué política esté fijada. Se investigó el código fuente instalado de `uvicorn` (`loops/asyncio.py`, `config.py:get_loop_factory`) para confirmar el mecanismo exacto antes de corregir.

**Fix real:** `Config.get_loop_factory()` acepta una ruta de import propia en `--loop`, no solo los nombres integrados. `app/main.py` expone `loop_factory()` (retorna `SelectorEventLoop`, funciona igual en Linux/macOS) para `--loop app.main:loop_factory`.

**Verificación tras el fix — servidor real, request real, HTTP real:**

```bash
uv run uvicorn app.main:app --loop app.main:loop_factory --port 8000
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/requests -H "Content-Type: application/json" \
  -d '{"customer_id":"FER-1001","raw_text":"Necesito 20 cascos modelo HX-200 ... 8% de descuento."}'
```
```
{"status":"ok"}
{"id":"8c6e3624-...","outcome":"DRAFT_READY", ...
 "quote":{"subtotal":"900.00","discount_amount":"72.00","net":"828.00",
          "tax_amount":"149.04","total":"977.04", ...},
 "audit_trail":[10 eventos: ingest -> extract -> resolve_customer ->
   validate_request -> resolve_catalog -> check_inventory -> price_quote ->
   evaluate_policy -> compose_draft -> finalize], ...}
```

Cifras exactas de AC-01 (900.00 → 828.00 neto → 977.04 total), montos como string decimal en la respuesta HTTP real (no solo en el schema), los 10 nodos en el orden correcto.

**Suite completa y calidad:**

```bash
uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy app/domain app/graph/state.py
```
```
139 passed in 31.41s
All checks passed!
40 files already formatted
Success: no issues found in 9 source files
```

**Documentación corregida por este hallazgo:** `CLAUDE.md` §7, `ADR-003` (consecuencias) y `README.md` (comando de arranque) — los tres tenían el fix de T11 documentado como suficiente; ahora reflejan la limitación real y el fix verificado.

**Contraste contra el frontend (`frontend/src/types/api.ts`):** cotejado campo por campo contra la respuesta real del `curl` de arriba — coincide exactamente, sin una sola discrepancia de nombre, anidamiento o nulabilidad. Es la confirmación de que `docs/API_CONTRACT.md` cumplió su propósito: dos sesiones delegadas que nunca se comunicaron entre sí (backend y frontend) produjeron formas compatibles, coordinadas únicamente por el documento del contrato. Verificación de extremo a extremo en navegador real (con `VITE_API_MODE=http` contra el servidor real) queda pendiente — ver `STATE.md`.

**Resultado:** ✅ `app/api/` completo. 139/139 tests, servidor real arrancado y probado por HTTP genuino, no solo por el harness de tests.

---

## E-12 · Validación desde un clon limpio (criterio A1) y demo end-to-end

**Método:** `git clone` del remoto a un directorio nuevo, sin ningún estado del entorno de desarrollo, siguiendo el `README.md` al pie de la letra. Es el criterio A1 de `PROJECT.md`.

```bash
git clone https://github.com/guisa17/quoteflow.git <dir-limpio>
```

### Bug encontrado — el `.env` no se leía

Siguiendo el paso 2 del README (`cp .env.example .env` en la raíz) y arrancando el backend desde `backend/`, se comprobó con un canario (`LOG_LEVEL=CANARIO`) que **el `.env` de la raíz nunca se leía**:

```
log_level = INFO      <- el valor de .env era CANARIO
```

`SettingsConfigDict(env_file=".env")` resuelve la ruta contra el **directorio de trabajo**, y el backend se ejecuta desde `backend/`, no desde la raíz donde vive el `.env`. Lo insidioso no es que fallara ruidosamente, sino lo contrario: los defaults de `Settings` coinciden con `.env.example`, así que **la aplicación parecía funcionar perfectamente mientras ignoraba en silencio cualquier valor que el usuario editara**. Alguien apuntando `DATABASE_URL` a otro Postgres habría visto sus datos ir al de siempre, sin un solo mensaje de error.

Nunca se detectó en desarrollo porque en ese entorno existía además un `backend/.env` creado durante T1 — funcionaba por accidente.

**Fix:** `app/config.py` resuelve rutas absolutas desde la ubicación del propio módulo, no desde el cwd, y acepta ambas ubicaciones (`raíz/.env` y `backend/.env`, esta última con precedencia para permitir un override local). Verificado con el mismo canario:

```
log_level = CANARIO   <- ahora sí lee el .env de la raíz
```

Este bug es la justificación entera de validar desde un clon limpio: 139 tests en verde no lo detectaron, porque ninguno depende de un valor de `.env` distinto al default.

### Suite completa desde el clon limpio

```bash
cd backend && uv sync && uv run pytest -q
```
```
139 passed in 43.21s
```

```bash
cd frontend && pnpm install && pnpm test && pnpm typecheck && pnpm build
```
```
Test Files  1 passed (1)
     Tests  11 passed (11)
$ tsc -b --noEmit
✓ built in 11.07s
```

`pnpm install` corrió limpio, sin el prompt de aprobación de `esbuild` que apareció en desarrollo — `pnpm-workspace.yaml` (comiteado en E-10) ya lo resuelve.

### Demo end-to-end: frontend real contra API real

Ambos levantados desde el clon limpio, con `VITE_API_MODE=http`. CORS verificado con un preflight real:

```
access-control-allow-origin: http://localhost:5173
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
```

Casos representativos, todos vía HTTP con el `Origin` del navegador:

| Caso | Resultado real |
|------|----------------|
| **S1** estándar | `DRAFT_READY` · subtotal 900.00 · desc. 72.00 · **neto 828.00** · IGV 149.04 · **total 977.04** · 10 nodos en la traza · borrador generado |
| **S2** incompleto | `NEEDS_CLARIFICATION` / `MISSING_QUANTITY` · `quote: null` (no cotizó) |
| **S8** inyección de prompt | `REJECTED_BY_POLICY` / `DISCOUNT_ABOVE_HARD_CEILING` · `human_decision: null` (nunca auto-aprobado) |
| **RF-02** bandeja | 39 solicitudes listadas con `outcome`, motivo y resumen |

### Reanudación durable a través de la API, con caída real del proceso

El escenario que sostiene el criterio "reanudación durable", esta vez extremo a extremo por HTTP:

1. `POST /requests` con S3 → `PENDING_APPROVAL` / `THRESHOLD_EXCEEDED`, neto 12 900.00
2. **Backend detenido a la fuerza** (`Stop-Process -Force`) — confirmado que deja de responder
3. Backend levantado de nuevo: **proceso completamente nuevo**
4. `GET /requests/{id}` desde el proceso nuevo:
   ```
   outcome recuperado : PENDING_APPROVAL / THRESHOLD_EXCEEDED
   neto preservado    : 12900.00
   traza preservada   : 8 eventos
   ```
5. `POST /requests/{id}/decision` con `APPROVE`:
   ```
   outcome final     : DRAFT_READY
   borrador          : generado
   decision auditada : jefe.ventas / dec-fase3-clon-limpio
   traza final       : 12 eventos
   total             : 15222.00
   ```
6. **Idempotencia a nivel HTTP** — mismo `decision_id` reenviado:
   ```
   HTTP 200 (nunca 409) · outcome DRAFT_READY · total 15222.00 (idéntico)
   ```

Un proceso que nunca escribió ese estado lo recuperó íntegro de Postgres y completó la ejecución. Es la demostración más fuerte del checkpointer persistente (ADR-003): no una simulación dentro de un test, sino una caída real entre dos peticiones HTTP.

**Resultado:** ✅ Criterio A1 satisfecho, con un bug real encontrado y corregido en el proceso. La aplicación se levanta y se recorre completa siguiendo solo el README, desde un clon limpio.

### Reporte Graphify regenerado sobre el código final

El reporte de E-09 se generó durante la Fase 1 y quedó anclado a un commit anterior — su propia sección *Graph Freshness* lo delata. No conocía `app/api/` ni `main.py`, así que describía un sistema incompleto. Regenerado:

```bash
graphify extract backend/app --code-only && graphify cluster-only backend/app
```
```
found 31 code files          (antes 26)
265 nodes · 588 edges · 15 communities   (antes 199 · 403 · 16)
Import Cycles: None detected.
```

Lo que cambia con la capa API incluida: `QuoteState` sigue siendo el nodo más conectado (38 aristas, antes 30), `decide_request` y `build_graph` aparecen como comunidades propias, y `to_request_detail()` entra en el top 10 de nodos más conectados — coherente con que sea el único punto de traducción entre el dominio y el contrato HTTP. **Sigue sin haber ciclos de import**, que es la comprobación estructural de que la frontera de ADR-002 se sostiene. `IMPACT.md` §3 actualizado con estas cifras.

## E-13 · Revisión posterior: defectos reproducidos, corregidos y verificados

**Objetivo:** corregir los defectos encontrados al revisar el proyecto con la aplicación corriendo. Cada uno se reprodujo primero contra la API real, y cada test de regresión se vio fallar antes de la corrección.

| Defecto reproducido | Corrección | Regla |
|---|---|---|
| 80 + 1 `RP-300` con 80 disponibles ⇒ `DRAFT_READY` | Stock comparado con la cantidad acumulada por SKU | BR-13 |
| "20 HX-200 y GL-500" cotizaba **200** `GL-500`, tomando los dígitos del SKU anterior | La ventana de cantidad empieza después del SKU anterior; un número seguido de `%` no es cantidad | BR-01 |
| `OBSERVE` y luego `APPROVE` con el mismo `decision_id` aprobaba, y la auditoría decía "sin efecto" | `409` en la API; el grafo tampoco reemplaza la decisión vigente | BR-15, BR-19 |
| `APPROVE` y `REJECT` simultáneos: ambos `200`, y uno desaparecía sin rastro | Bloqueo de la fila y `409` para el perdedor | BR-19 |
| Actor y `decision_id` vacíos aprobaban; se aceptaba 1 MB de texto | Límites de entrada, `422` | BR-20 |
| Bandeja atrasada para siempre si el proceso caía tras reanudar el grafo | Cualquier decisión posterior sobre el caso la repara | RF-02 |
| `/health` siempre `200`; checkpointer con una sola conexión | `/health` consulta los dos pools; checkpointer con pool | RNF-06 |
| 15 alertas en dependencias de frontend y 7 en backend | `axios` 1.21.0, `follow-redirects` 1.16.2, `langgraph-checkpoint-postgres` 3.2.0, `langgraph-sdk` 0.4.14, `urllib3` 2.8.0, `certifi` 2026.10.23 | — |

**Hallazgo que la suite no detectó:** el primer test de resiliencia solo cortaba conexiones con Postgres encendido, y pasaba. Con un reinicio real, el backend tardó **127 s** en responder:

```text
up: 200
down: 503
postgres healthy; polling backend
t=   3.1s health=503
t= 126.7s health=200
create after recovery: 201
```

El primer intento de corrección (`reconnect_timeout` corto) lo empeoró: sin recuperación en 120 s, en las dos corridas. Tras leer el código fuente de `psycopg_pool`, la corrección fue `pool.check()` cada 2 s, sin cancelar operaciones del pool desde `/health`. Salida tras la corrección, medida desde que Postgres queda `healthy`, en las tres corridas:

```text
down: 503
postgres healthy; polling backend
t=   0.0s health=200
create after recovery: 201
```

**Recorrido con procesos reales:** dos `uvicorn` contra Postgres en Docker, HTTP real.

```text
PASS  S1 cifras  977.04
PASS  stock acumulado  Disponible de RP-300: 80. Solicitado: 81.
PASS  sin cantidad inventada  MISSING_QUANTITY
PASS  actor vacio 422
PASS  cuerpo enorme 422
PASS  OBSERVE 200
PASS  mismo id otra accion 409
PASS  sigue pendiente
PASS  carrera 2 procesos x10: un ganador  {'REJECTED_BY_POLICY': 6, 'DRAFT_READY': 4}
PASS  estado recuperado tras matar backend
PASS  aprobar tras reinicio
PASS  reenvio identico
PASS  health 503 con Postgres caido  503 en 2.0s
PASS  health vuelve a 200 sin reiniciar backend
PASS  crear tras el corte  201
PASS  decidir tras el corte

FALLOS: ninguno
```

**Suites y auditorías:**

```bash
uv run pytest                 # 178 passed in 60.29s
uv run ruff check .           # All checks passed!
uv run ruff format --check .  # 45 files already formatted
uv run mypy app/domain app/graph/state.py  # Success: no issues found in 10 source files
pnpm test                     # Tests 21 passed (21)
pnpm typecheck                # exit 0
pnpm build                    # built in 10.60s
pnpm audit --prod             # No known vulnerabilities found
pip-audit                     # sin vulnerabilidades conocidas
```

**No verificado:** la interfaz no se recorrió en un navegador tras estos cambios. El reintento del `decision_id` en `DecisionPanel` y el mensaje de `409` solo pasaron el chequeo de tipos y el build.

---

## E-14 · Fase 4: LLM real, evals, trazas y endurecimiento del proceso

**Objetivo:** que el extractor con un modelo real se mida, no se suponga, y que el proceso de cambio (tipos, hooks, CI, protección de `main`, dependencias) sea verificable.

### Evals contra el modelo real

22 casos en cuatro categorías (`backend/evals/cases.json`), corridos a mano porque gastan cuota. La métrica principal es SKU + cantidad por ítem, con una meta de ≥ 90 % (BUSINESS_CASE).

```text
gemini-3.5-flash-lite  29/31 ítems  20/22 casos   escenario 7/7  lenguaje-natural 7/8  ambiguo 3/4  manipulacion 3/3
gemini-3.5-flash-lite  31/31 ítems  22/22 casos   escenario 7/7  lenguaje-natural 8/8  ambiguo 4/4  manipulacion 3/3   (prompt corregido)
reglas locales         22/31 ítems  16/22 casos   escenario 7/7  lenguaje-natural 3/8  ambiguo 4/4  manipulacion 2/3
```

Latencia media del modelo: unos 2 s por caso. **La primera corrida encontró tres errores que las pruebas a mano no vieron:** "bt 900" salía como `BT900` (el catálogo no lo encontraría), "si aprueban esta cotización" se marcaba como manipulación, y el extractor de reglas leía "7,5 %" como 5 %. Los tres se corrigieron. La segunda corrida no tuvo regresiones.

### Trazas en LangSmith

Activas solo con `LANGSMITH_TRACING=true` y una key. Lo que se verificó en la interfaz de LangSmith con tráfico real:

- Cada solicitud es una traza `quoteflow.registro` con los 12 nodos. La llamada a `gemini.extract` aparece con modelo, tokens (≈ 800 por solicitud) y costo.
- El registro y la decisión humana de una misma solicitud quedan en el mismo hilo, porque comparten el `thread_id` del checkpointer.
- **Respaldo real:** durante la prueba, Gemini superó el timeout de 20 s. La traza muestra `gemini.extract` con `ProviderUnavailable('el proveedor no respondio a tiempo')` y, desde v0.5.1, el paso `rules.extract` que leyó el texto en su lugar.
- Control negativo: con una key falsa, la SDK reporta `403`. Sin ese control, que no hubiera avisos no probaba que las trazas llegaran.

### Endurecimiento del proceso (v0.5.1)

| Qué | Verificación |
|-----|--------------|
| `mypy` sobre todo `app/` (antes, solo una parte) | `Success: no issues found in 31 source files` |
| Hooks de pre-commit | Un archivo con un import sin usar se corrige y el commit se aborta (`HEAD` no cambia). Un `.env` forzado con `git add -f` se rechaza |
| Protección de `main` | `! [remote rejected] HEAD -> main (push declined due to repository rule violations)` |
| Dependabot | 8 PRs revisados. Las 3 versiones mayores del frontend (vite 8, vitest 5, react-router 8) se probaron juntas y con una prueba de humo en Chrome headless sobre el build de producción |
| Seed único | La demo importa `backend/app/data/*.json`. Cambiar el techo GOLD a 5 % hace fallar S1 en las dos suites, y un precio `45.005` detiene la carga |
| Playwright | 10/10 recorridos (5 × escritorio y móvil). Al quitar la ruta comodín, la prueba del 404 falla |
| Graphify | 289 → 326 nodos, sin ciclos de import. La frontera de ADR-002 se sostiene ([docs/graphify/](../graphify/README.md)) |

**Suites y auditorías** (backend en el CI con Postgres 16; frontend y auditorías en local):

```bash
uv run pytest                 # 214 passed, 1 warning in 12.56s
uv run ruff check .           # All checks passed!
uv run ruff format --check .  # 54 files already formatted
uv run mypy app               # Success: no issues found in 31 source files
pnpm test                     # Tests 35 passed (35)
pnpm typecheck                # exit 0
pnpm audit --prod             # No known vulnerabilities found
uvx pip-audit                 # No known vulnerabilities found
```

**No verificado en local:** la suite de integración del backend, porque Docker Desktop no arrancó durante esta sesión ("Docker Desktop is unable to start"), igual que en E-08. Las pruebas unitarias pasaron en local (161) y la suite completa pasó en el CI. **Cerrado el 2026-11-10:** con Docker de vuelta, la suite completa pasó también en local (`214 passed, 1 warning in 63.14s`).

---

## E-15 · Proveedor de LLM intercambiable (ADR-006)

**Objetivo:** que el extractor real acepte cualquier proveedor con `LLM_MODEL=proveedor:modelo`, sin cambiar la frontera de ADR-002 ni el respaldo de ADR-004, y medirlo con las mismas evals.

**Evals con la key de Gemini, por tres caminos** (después de repetir los casos que el proveedor no respondió):

```text
gemini:gemini-3.5-flash-lite          31/31 ítems  22/22 casos   REST nativo, sin cambios de comportamiento
google_genai:gemini-3.5-flash-lite    31/31 ítems  22/22 casos   LangChain + langchain-google-genai
openai:gemini-3.5-flash-lite          31/31 ítems  22/22 casos   LangChain + endpoint compatible con OpenAI
```

En la primera pasada, Gemini estaba inestable: `503` o más de 20 s en 2, 4 y 2 casos, también por el camino nativo, que no cambió. Todos esos fallos se clasificaron como `ProviderUnavailable` y ningún caso respondido salió mal leído.

**Arranque con una configuración imposible** (`uvicorn` real, `LLM_MODE=real`):

```text
LLM_MODEL=claude-sonnet-5     LLMConfigError: LLM_MODEL='claude-sonnet-5' no tiene la forma proveedor:modelo (...)
LLM_MODEL=inventado:x         LLMConfigError: Unsupported provider='inventado'.
LLM_MODEL=groq:llama-3.3-70b  LLMConfigError: Falta el paquete del proveedor 'groq': uv add langchain-groq
```

El primer valor es el que dejaba la plantilla antigua de `.env.example`; sin esta validación, el sistema habría intentado usar Anthropic sin key y habría caído en silencio al respaldo.

**De punta a punta:** backend real con `LLM_MODEL=google_genai:gemini-3.5-flash-lite`. `POST /requests` con "mándennos dos docenas de cascos hx 200 para la planta de Arequipa" → `201`, `DRAFT_READY`, línea `HX-200 × 24`. La auditoría de `extract` dice `Intento 1: 1 item(s) extraído(s) con gemini-3.5-flash-lite`.

**Suites:**

```bash
uv run pytest tests/unit      # 188 passed (27 nuevas en test_llm_providers.py)
uv run ruff check .           # All checks passed!
uv run mypy app               # Success: no issues found in 33 source files
```

**No verificado con un modelo real:** Anthropic, OpenAI y Ollama. Están probados con dobles (`tests/unit/test_llm_providers.py`) y quedan "soportados, no medidos" hasta correr las evals con una key de cada uno.

---

## Limitaciones de la Fase 0

Lo siguiente **no** está verificado. Se declara aquí en lugar de presentarse como hecho:

| # | Limitación |
|---|------------|
| ~~L-01~~ | ~~Ninguna regla de negocio implementada ni probada~~ — **resuelto**: 130 tests, dominio (T2-T6), grafo (T7-T11) y cobertura sistemática (T12-T14) completos |
| ~~L-02~~ | ~~Reanudación solo demostrada dentro del mismo proceso~~ — **resuelto**: T13 descarta y reconstruye grafo y checkpointer entre interrumpir y reanudar (E-09) |
| ~~L-03~~ | ~~El `README.md` no se ha validado desde un clon limpio~~ — **resuelto en E-12**: validado desde un `git clone` real, con un bug de `.env` encontrado y corregido en el proceso |
| ~~L-04~~ | ~~El mapa de `IMPACT.md` es de diseño~~ — **resuelto**: contrastado contra el reporte Graphify real (E-09) y ampliado con `app/api/` tras la Fase 2 |
| L-05 | ~~**La calidad de la extracción con un modelo real es desconocida**~~ **Cerrada:** el extractor con Gemini (`gemini-3.5-flash-lite`) resuelve los 8 escenarios y casos en lenguaje natural ("dos docenas" = 24). Ver [ROADMAP.md](../ROADMAP.md) Fase 4. Las pruebas siguen sin depender del modelo (`httpx.MockTransport`) |
| ~~L-06~~ | ~~El repositorio aún no está bajo control de versiones~~ — **resuelto**: remoto en `github.com/guisa17/quoteflow` |
| L-07 | El backend tiene andamiaje (`config.py`, paquetes vacíos) pero ningún módulo de dominio, grafo ni API con lógica real |
| L-08 | **Sin autenticación:** cualquiera con acceso a la API puede aprobar, y `actor` es texto que declara el cliente, así que la auditoría no prueba quién decidió |
| ~~L-09~~ | ~~No hay pruebas end-to-end en navegador~~ — **resuelto**: Playwright recorre la bandeja, el registro, la aprobación humana, BR-18 y el 404, en escritorio y móvil, también en el CI |

## Deuda aceptada

Decisiones conscientes de no hacer, no descuidos. Se registran para que quien retome el proyecto no las confunda con trabajo pendiente:

| # | Deuda | Razón |
|---|-------|-------|
| D-01 | Sin escalas de precio por volumen | Una segunda dimensión de descuento interactúa con la política por nivel y vuelve el cálculo difícil de auditar manualmente. Declarado fuera de alcance |
| D-02 | Sin paginación en la bandeja | El volumen del MVP no la justifica |
| D-03 | Sin reintentos con espera progresiva ante fallo del modelo | Un fallo de extracción degrada a `NEEDS_CLARIFICATION` con el error registrado, que es el comportamiento seguro (RF-05) |
| D-04 | Borrador en un solo idioma | El caso de negocio es local; la internacionalización no aporta al criterio evaluado |
| D-05 | `mypy` sin modo estricto | Desde v0.5.1 revisa todo `app/` (antes, solo `app/domain` y `app/graph/state.py`). El modo estricto no aporta garantías adicionales sobre lo que sostiene el Definition of Done |

---

## Siguiente paso

El estado vigente y el siguiente incremento están en [STATE.md](STATE.md). Cada cambio relevante añade su comando y salida real a este documento, en el mismo ciclo en que se implementa.

---

**Relacionados:** [STATE.md](STATE.md) · [PHASE_01.md](PHASE_01.md) · [LOOP.md](LOOP.md) · [AI_USE.md](AI_USE.md)
