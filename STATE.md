# STATE — QuoteFlow

Estado real del proyecto: qué está construido, qué está verificado, qué está bloqueado y cuál es el siguiente paso.

Criterio de handoff: **otra persona puede continuar desde aquí sin reconstruir el contexto.** Si este documento y el código discrepan, uno de los dos está mal y se corrige en el mismo ciclo.

**Última actualización:** 2026-11-09

---

## Situación

| | |
|---|---|
| **Fases** | **1, 2 y 3 completas.** El MVP funciona de punta a punta |
| **Repositorio** | [github.com/guisa17/quoteflow](https://github.com/guisa17/quoteflow) (privado) |
| **Aplicación** | Ejecutable de punta a punta y **validada desde un clon limpio**: backend (178 tests) + API HTTP + frontend (21 tests) |
| **Verificación clave** | Reanudación durable demostrada con una **caída real del backend** entre dos peticiones HTTP, no simulada en un test |

## Qué está construido

| Área | Artefactos | Estado |
|------|-----------|--------|
| **Negocio** | [BUSINESS_CASE.md](BUSINESS_CASE.md) · [IMPACT.md](IMPACT.md) | ✅ |
| **Proyecto** | [PROJECT.md](PROJECT.md) · [REQUIREMENTS.md](REQUIREMENTS.md) · [ROADMAP.md](ROADMAP.md) · [PHASE_01.md](PHASE_01.md) · [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | ✅ |
| **Decisiones** | [ADR-001](docs/adr/ADR-001-datos-ficticios-propios.md) · [ADR-002](docs/adr/ADR-002-frontera-determinista.md) · [ADR-003](docs/adr/ADR-003-persistencia-checkpointer.md) | ✅ |
| **Gobierno** | [CLAUDE.md](CLAUDE.md) · [AI_USE.md](AI_USE.md) · [LOOP.md](LOOP.md) · [docs/REFERENCES.md](docs/REFERENCES.md) · [docs/graphify/](docs/graphify/GRAPH_REPORT.md) | ✅ |
| **Verificación** | [EVIDENCE.md](EVIDENCE.md) — 12 secciones con salida real (E-01…E-12) | ✅ |
| **Dominio determinista** | `enums`, `models`, `repositories`, `pricing`, `policy`, `validation`, `tools` | ✅ T2-T6 |
| **Grafo LangGraph** | `state`, `llm/`, `nodes`, `routing`, `checkpointer`, `build` | ✅ T7-T11 |
| **Integración sistemática** | 8 escenarios, reinicio real, idempotencia | ✅ T12-T14 |
| **API HTTP** | `app/api/` — 4 endpoints + tabla `requests`, servidor real verificado | ✅ |
| **Frontend** | `frontend/` — React + Vite + shadcn/ui, modo mock y modo HTTP real | ✅ |

**178 tests de backend + 21 de frontend, `ruff`/`ruff format`/`mypy` limpios, sin LLM externo ni credenciales.**

## Decisiones vigentes

| # | Decisión | Registro |
|---|----------|----------|
| 1 | Datos de dominio ficticios y versionados | ADR-001 |
| 2 | El LLM interpreta y redacta; el dominio calcula y decide | ADR-002 |
| 3 | Se implementan los 5 resultados; la profundidad de pruebas va a los 3 flujos principales | PROJECT §2.1 |
| 4 | El umbral de USD 10 000 se evalúa sobre el neto tras descuento, antes de IGV | REQUIREMENTS BR-05 |
| 5 | Techo duro de descuento del 20 % que **no** es aprobable | REQUIREMENTS BR-07 |
| 6 | Cliente desconocido ⇒ nivel conservador STANDARD más revisión humana | REQUIREMENTS BR-08 |
| 7 | Sin escalas de precio por volumen | BUSINESS_CASE §4 |
| 8 | Un solo hilo de gobierno; trabajo paralelo real cuando hay aislamiento de archivos y verificación independiente | AI_USE §1 |
| 9 | Prácticas de GSD adoptadas sin instalar `gsd-core` | AI_USE §1 |
| 10 | `CLAUDE.md` en lugar de `AGENTS.md` | CLAUDE.md |
| 11 | `AsyncPostgresSaver` como checkpointer; `MemorySaver` solo en pruebas unitarias | ADR-003 |
| 12 | Las cinco herramientas locales de dominio las invocan los nodos, no el modelo | PROJECT §4.2.1 |
| 13 | BR-02 ("sin espacios sobrantes") = "sin espacios, punto" | EVIDENCE E-06 |
| 14 | Dominio en la sesión principal; grafo y frontend delegados a Sonnet, briefeados solo con documentos del repo | AI_USE §1 |
| 15 | Event loop en Windows: `loop_factory()` propio vía `--loop`, porque `uvicorn` ignora la política de `asyncio` — el fix inicial de T11 era insuficiente | EVIDENCE E-11 |
| 16 | Contrato de API fijado antes de escribir código en ambos lados — confirmado sin discrepancias al cruzarlo contra el frontend | docs/API_CONTRACT.md, EVIDENCE E-11 |
| 17 | `bento-app` como referencia de principios de diseño, no como plantilla | AI_USE §2 |
| 18 | AC-11: rechazo humano ⇒ `REJECTED_BY_POLICY`. Se corrigió la especificación, no el código | EVIDENCE E-09 |
| 19 | Tipos de `QuoteState` registrados en el serializador msgpack del checkpointer | EVIDENCE E-09 |
| 20 | AC-10 verificado vía `OBSERVE` a nivel de grafo y por reenvío de `decision_id` a nivel HTTP | EVIDENCE E-09/E-11 |
| 21 | Frontend con `pnpm`; su verificación ad-hoc reemplazada por una suite Vitest real | EVIDENCE E-10 |
| 22 | Advisory de `react-router` (CSRF modo RSC) re-verificado por grep — no aplica a un SPA sin RSC | EVIDENCE E-10 |
| 23 | `LOOP.md` aún sin ejecutar: el modo de test sin modelo externo (`LLM_MODE=fake`) permite verificar todo el flujo | LOOP.md |
| 24 | `GET /requests` lee solo la tabla de cache, nunca reconstruye cada solicitud desde el checkpointer | ADR-003, `app/api/store.py` |
| 25 | `Settings` resuelve el `.env` por ruta absoluta desde el módulo, no relativa al cwd — el `.env` de la raíz nunca se leía al arrancar desde `backend/` | EVIDENCE E-12 |
| 26 | Stock comparado con la cantidad acumulada por SKU | REQUIREMENTS BR-13, EVIDENCE E-13 |
| 27 | Una decisión contradictoria responde `409` y no se aplica; las decisiones se serializan bloqueando la fila de la solicitud | REQUIREMENTS BR-19, EVIDENCE E-13 |
| 28 | Límites de entrada en la API | REQUIREMENTS BR-20 |
| 29 | Pools con mantenimiento periódico; `/health` consulta Postgres de verdad | `app/db.py`, EVIDENCE E-13 |

## Verificado

| Qué | Cómo | Resultado |
|-----|------|-----------|
| Suite completa de backend | `pytest` (unit + integración + API) | ✅ **178/178** |
| Frontend | `pnpm test` · `typecheck` · `build` | ✅ **21/21**, limpio |
| **Decisiones simultáneas entre dos procesos** | Carrera `APPROVE`/`REJECT` contra dos `uvicorn`, 10 veces | ✅ un ganador en cada una |
| **Reinicio real de Postgres con el backend encendido** | `docker stop` / `docker start` | ✅ `503` durante el corte; responde en cuanto Postgres vuelve, sin reiniciar el backend |
| Dependencias de producción | `pip-audit` · `pnpm audit --prod` | ✅ sin vulnerabilidades conocidas (2026-11-09) |
| `ruff` / `ruff format` / `mypy` | Dominio, grafo y API | ✅ limpios |
| **Aplicación desde un clon limpio** | `git clone` real + README al pie de la letra | ✅ **encontró un bug** (`.env`), corregido |
| **Demo end-to-end, frontend real ↔ API real** | `VITE_API_MODE=http`, CORS verificado, S1/S2/S8 vía HTTP | ✅ cifras exactas |
| **Reanudación durable con caída real del proceso** | `PENDING_APPROVAL` → matar backend → reiniciar → estado recuperado → aprobar | ✅ `DRAFT_READY` |
| **Idempotencia a nivel HTTP** | Mismo `decision_id` reenviado | ✅ HTTP 200, resultado idéntico |
| Integridad de la documentación | Recorrido automatizado de enlaces relativos | ✅ 0 rotos |

Detalle completo en [EVIDENCE.md](EVIDENCE.md). Los dos hallazgos más importantes del proyecto (E-11 el `loop_factory` de `uvicorn`, E-12 el `.env` no leído) **no los detectó la suite de tests** — aparecieron al arrancar el proceso real y al clonar en limpio.

## Limitaciones conocidas

Declaradas, no ocultas — detalle y deuda aceptada en [EVIDENCE.md](EVIDENCE.md):

| # | Limitación |
|---|------------|
| L-05 | Todo corre con `LLM_MODE=fake`: la calidad de extracción con un modelo real es desconocida. El ciclo para cerrarla está definido en [LOOP.md](LOOP.md) |
| L-08 | **Sin autenticación:** cualquiera con acceso a la API puede aprobar, y `actor` es texto que declara el cliente, así que la auditoría no prueba quién decidió. No exponer la API con datos reales antes de resolverlo |
| L-09 | Los 21 tests de frontend prueban el motor mock; no hay pruebas de componentes ni end-to-end en navegador |
| D-01…D-05 | Sin escalas de precio por volumen, sin paginación, sin reintentos con espera progresiva, borrador en un solo idioma, `mypy` no estricto — todas con su razón registrada |

## Si alguien retoma este proyecto

El siguiente incremento con más valor, en orden:

1. **Ejecutar [LOOP.md](LOOP.md)** — construir `app/llm/anthropic_extractor.py` contra el `Protocol` ya definido y endurecerlo contra los 8 escenarios. Es el único componente no determinista del sistema y ya tiene worker, verifier, presupuesto y condición de bloqueo definidos.
2. **Reemplazar el seed por una fuente real** — los cuatro repositorios de `app/domain/repositories.py` son la única frontera a tocar; ni el grafo ni las reglas cambian ([ADR-001](docs/adr/ADR-001-datos-ficticios-propios.md)).
3. **Paginación en la bandeja** (D-02) cuando el volumen la justifique.

Puerta de entrada: [CLAUDE.md](CLAUDE.md) (reglas) y este documento (estado). Ambos se leen de forma autónoma, sin depender de ninguna conversación previa.

---

**Relacionados:** [README.md](README.md) · [EVIDENCE.md](EVIDENCE.md) · [ROADMAP.md](ROADMAP.md) · [PROJECT.md](PROJECT.md) · [REQUIREMENTS.md](REQUIREMENTS.md) · [AI_USE.md](AI_USE.md) · [IMPACT.md](IMPACT.md)
