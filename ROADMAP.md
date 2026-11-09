# ROADMAP — QuoteFlow

Cuatro fases. Cada una entrega algo verificable por sí mismo; ninguna deja trabajo a medias que la siguiente deba terminar.

El orden responde a una regla: **lo que no se puede improvisar al final va primero.** El dominio determinista y la persistencia sostienen los criterios del Definition of Done; la interfaz es la capa más recortable.

---

## Fase 0 — Encuadre y especificación ✅

**Objetivo:** que exista una definición de "correcto" antes de escribir código.

| Entregable | Estado |
|------------|--------|
| Seed de dominio ficticio calibrado (`backend/app/data/`) | ✅ |
| `BUSINESS_CASE.md`, `PROJECT.md`, `REQUIREMENTS.md` | ✅ |
| `ADR-001` (datos ficticios), `ADR-002` (frontera determinista) | ✅ |
| `CLAUDE.md`, `AI_USE.md`, `LOOP.md`, `STATE.md` | ✅ |
| Andamiaje: `.gitignore`, `.env.example`, `docker-compose.yml`, `README.md` | ✅ |

**Definition of Done:** los 8 escenarios del seed alcanzan su `expected_outcome` por cálculo manual, y cada regla de negocio tiene un identificador citable desde el código.

---

## Fase 1 — Vertical funcional ✅

**Objetivo:** que una solicitud recorra el flujo completo hasta un estado terminal, incluyendo pausa y reanudación durable, verificado por pruebas automatizadas.

Es la fase que sostiene el Definition of Done del proyecto. Detalle en [PHASE_01.md](PHASE_01.md).

| Entregable | Sostiene | Estado |
|------------|----------|--------|
| `app/domain/` — modelos, repositorios, precios, política, validación | RF-06, BR-01…13 | ✅ |
| `app/graph/` — estado tipado, nodos, routing, checkpointer Postgres | RF-07, RNF-01, RNF-02 | ✅ |
| `app/llm/` — extractor determinista para pruebas (extractor real: [LOOP.md](LOOP.md), fuera de esta fase) | RF-05, RF-10 | ✅ |
| `tests/unit` + `tests/integration` | AC-01…AC-11 | ✅ 130 tests |

**Definition of Done:** ✅ `uv run pytest` en verde sin acceso a un modelo externo (130/130), incluyendo interrupción, reanudación tras reinicio *real* del proceso e idempotencia. Evidencia completa en [EVIDENCE.md](EVIDENCE.md) E-06…E-09.

**Riesgo que se materializó:** una caída real de Docker Desktop durante T11 (motor sin CPUs asignados) — resuelta con un reinicio del sistema, sin pérdida de trabajo. Detalle en EVIDENCE.md E-08. El riesgo original de la extracción (único componente no determinista) sigue acotado por el ciclo de [LOOP.md](LOOP.md), todavía no ejecutado — el extractor de pruebas (`FakeExtractor`) ya resuelve los 8 escenarios sin necesitarlo.

---

## Fase 2 — Superficie de uso ✅

**Objetivo:** que el flujo sea operable por una persona, no solo por una prueba.

| Entregable | Sostiene | Estado |
|------------|----------|--------|
| `app/api/` — registrar solicitud, bandeja, detalle, decisión humana | RF-01…RF-04 | ✅ 9 tests de integración, servidor real verificado |
| `frontend/` — crear, bandeja, detalle con trazabilidad, panel de decisión | RF-09 | ✅ 11 tests, modo mock + cliente HTTP real |

**Definition of Done:** ✅ los cinco puntos de la interfaz mínima existen en el frontend; el detalle muestra extracción, cotización, riesgos y trazabilidad completa, no solo el resultado. Pendiente confirmar en navegador real con `VITE_API_MODE=http` (Fase 3).

**Hallazgo no anticipado:** el fix de event loop de Windows aplicado en T11 (Fase 1) resultó insuficiente para `uvicorn` real — solo se detectó al arrancar el servidor de verdad, no por la suite de tests. Corregido; detalle en `EVIDENCE.md` E-11.

---

## Fase 3 — Evidencia y cierre ✅

**Objetivo:** que otra persona pueda verificar lo que el repositorio afirma.

| Entregable | Sostiene | Estado |
|------------|----------|--------|
| `EVIDENCE.md` con comandos y salidas reales | "Documentación viva" | ✅ 12 secciones (E-01…E-12) |
| `IMPACT.md` verificado contra el código construido | Mapa de impacto | ✅ contrastado con Graphify real + `app/api/` |
| `README.md` validado desde un clon limpio | "Aplicación ejecutable" | ✅ `git clone` real — **encontró un bug** (E-12) |
| Guion de demo: casos estándar, incompleto y con aprobación | "Casos representativos" | ✅ README, cifras verificadas contra el sistema real |

**Definition of Done:** ✅ los criterios de aceptación tienen evidencia asociada en `EVIDENCE.md`, y las limitaciones declaradas coinciden con el estado real del código.

**Hallazgo que justificó la fase:** validar desde un clon limpio reveló que el `.env` de la raíz nunca se leía — la aplicación *parecía* funcionar porque los defaults coincidían con `.env.example`, así que cualquier valor editado se ignoraba en silencio. 139 tests en verde no lo detectaron. Detalle en `EVIDENCE.md` E-12.

---

## Fuera del roadmap

No son fases pendientes: son decisiones de no hacer, registradas en [BUSINESS_CASE.md §4](BUSINESS_CASE.md) y [PROJECT.md §2.3](PROJECT.md). Envío automático al cliente, autenticación empresarial, integraciones reales, facturación, reserva efectiva de stock, escalas de precio por volumen, infraestructura productiva.

---

**Relacionados:** [PHASE_01.md](PHASE_01.md) · [STATE.md](STATE.md) · [PROJECT.md](PROJECT.md) · [LOOP.md](LOOP.md)
