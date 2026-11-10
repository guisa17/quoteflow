# STATE — QuoteFlow

Estado real del proyecto: qué está construido, qué está verificado, qué falta y cuál es el siguiente paso.

Criterio de handoff: **otra persona puede continuar desde aquí sin reconstruir el contexto.** Si este documento y el código discrepan, uno de los dos está mal y se corrige en el mismo ciclo.

**Última actualización:** 2026-11-10 · versión **v0.5.1**

---

## Situación

| | |
|---|---|
| **Fases** | **0 a 4 completas** ([ROADMAP.md](../ROADMAP.md)). La Fase 4 agregó LLM real, detección de manipulación, CI, evals, trazas y la nueva interfaz |
| **Repositorio** | [github.com/guisa17/quoteflow](https://github.com/guisa17/quoteflow), `main` protegida: solo entra por pull request con el CI en verde |
| **Aplicación** | Backend (214 tests) + API HTTP + frontend (35 tests). Lee el texto con Gemini o, sin key, con un extractor de reglas |
| **Versiones** | `v0.4.0` (fases 0-3) · `v0.5.0` (Fase 4) · `v0.5.1` (endurecimiento del proceso). Releases en GitHub |

## Qué está construido

| Área | Artefactos | Estado |
|------|-----------|--------|
| **Negocio** | [BUSINESS_CASE.md](../BUSINESS_CASE.md) · [IMPACT.md](../IMPACT.md) | ✅ |
| **Proyecto** | [PROJECT.md](../PROJECT.md) · [REQUIREMENTS.md](../REQUIREMENTS.md) · [ROADMAP.md](../ROADMAP.md) · [PHASE_01.md](PHASE_01.md) · [API_CONTRACT.md](../API_CONTRACT.md) | ✅ |
| **Decisiones** | [ADR-001…005](../adr/) — datos ficticios, frontera determinista, checkpointer, Gemini con respaldo, manipulación a revisión humana | ✅ |
| **Gobierno** | [CLAUDE.md](../../CLAUDE.md) · [AI_USE.md](AI_USE.md) · [LOOP.md](LOOP.md) · [REFERENCES.md](../REFERENCES.md) · [Graphify](../graphify/README.md) | ✅ |
| **Verificación** | [EVIDENCE.md](EVIDENCE.md) — salidas reales, E-01…E-14 | ✅ |
| **Dominio determinista** | `enums`, `models`, `repositories`, `pricing`, `policy`, `validation`, `tools`, `manipulation` | ✅ |
| **Grafo LangGraph** | 12 nodos, interrupción humana, checkpointer en Postgres | ✅ |
| **Extracción** | Gemini con salida forzada por esquema; respaldo explícito al extractor de reglas | ✅ |
| **API HTTP** | `app/api/` — 4 endpoints + tabla `requests` | ✅ |
| **Frontend** | React 19 + Vite 8 + Tailwind 4; modo demo (motor en el navegador sobre el mismo seed) y modo HTTP | ✅ |
| **Calidad** | CI (GitHub Actions), pre-commit, Dependabot, Playwright, evals locales, trazas en LangSmith | ✅ |

## Decisiones vigentes

Las decisiones de arquitectura están en los ADRs. Las de proceso, en [CLAUDE.md](../../CLAUDE.md). Resumen de las que más condicionan el trabajo:

| # | Decisión | Registro |
|---|----------|----------|
| 1 | El LLM solo lee el texto; precios, política y aprobaciones son código determinista | ADR-002 |
| 2 | Si el proveedor del LLM no responde, lee el extractor de reglas y el folio lo dice: el respaldo nunca es silencioso | ADR-004 |
| 3 | Un intento de manipulación manda el caso a revisión humana; un rechazo por techo duro lo sigue dominando | ADR-005, BR-18 |
| 4 | El seed de dominio vive en `backend/app/data/` y la demo del frontend lo importa directamente, sin copia | ADR-001 |
| 5 | Las pruebas nunca llaman a un LLM real ni envían trazas; las evals contra el modelo real se corren a mano | RF-10, [evals/](../../backend/evals/README.md) |
| 6 | Conventional Commits, trabajo por ramas y unión solo por PR con el CI en verde | CLAUDE.md |
| 7 | `mypy` sobre todo `app/`, sin modo estricto | RNF-04 |

## Verificado

| Qué | Cómo | Resultado |
|-----|------|-----------|
| Suite de backend | `pytest` en el CI, con Postgres 16 real | ✅ **214/214** |
| Frontend | `pnpm test` · `typecheck` · `build` | ✅ **35/35**, limpio |
| **End-to-end en navegador** | Playwright, 5 recorridos en escritorio y en móvil, también en el CI | ✅ **10/10**; la prueba del 404 falla si se quita la ruta comodín |
| Lint, formato y tipos | `ruff` · `ruff format` · `mypy app` | ✅ limpios (31 archivos con mypy) |
| **Extractor con el modelo real** | `python -m evals.run`, 22 casos en 4 categorías | ✅ **31/31 ítems (100 %), 22/22 casos.** Meta ≥ 90 % |
| Extractor de reglas (el respaldo) | Los mismos 22 casos | 22/31 ítems (71 %): suficiente para los escenarios, no para el lenguaje natural |
| **Manipulación** | Escenario S8 + 3 casos de evals + prueba en vivo | ✅ marcada siempre; sin falsos positivos en casos legítimos |
| **Respaldo con caída real del proveedor** | Gemini superó el timeout durante una prueba en vivo | ✅ la solicitud se leyó con reglas y quedó etiquetada en LangSmith |
| Protección de `main` | Push directo a `main` | ✅ rechazado por GitHub |
| Hooks de pre-commit | Archivo con errores y `.env` forzado | ✅ los dos commits se rechazan |
| Dependencias | `pip-audit` · `pnpm audit --prod` | ✅ sin vulnerabilidades conocidas (2026-11-10) |
| Reanudación durable, idempotencia, carreras, reinicio de Postgres | Procesos reales | ✅ ver EVIDENCE E-09…E-13 |

Detalle completo en [EVIDENCE.md](EVIDENCE.md). Los hallazgos más importantes del proyecto no los detectó la suite: el `loop_factory` de `uvicorn` (E-11), el `.env` que nunca se leía (E-12), la recuperación de 127 s tras reiniciar Postgres (E-13) y los tres errores de extracción que encontraron las evals (E-14).

## Limitaciones conocidas

| # | Limitación |
|---|------------|
| L-08 | **Sin autenticación:** cualquiera con acceso a la API puede aprobar, y `actor` es texto que declara el cliente. No exponer la API con datos reales antes de resolverlo |
| P-01 | Una solicitud con varias sedes de entrega se cotiza hacia una sola ([ROADMAP.md](../ROADMAP.md)) |
| D-01…D-04 | Sin escalas por volumen, sin paginación, sin reintentos con espera progresiva, borrador en un solo idioma — con su razón en EVIDENCE |

## Si alguien retoma este proyecto

El siguiente incremento con más valor, en orden:

1. **P-01, varias sedes:** sede por línea y una regla que mande el caso a revisión. El plan por capas está en el ROADMAP.
2. **Autenticación** antes de cualquier uso con datos reales (L-08).
3. **Pruebas end-to-end contra la API real** (hoy corren en modo demo), con Postgres en el CI.

Puerta de entrada: [CLAUDE.md](../../CLAUDE.md) (reglas) y este documento (estado). Ambos se leen de forma autónoma, sin depender de ninguna conversación previa.

---

**Relacionados:** [README.md](../../README.md) · [EVIDENCE.md](EVIDENCE.md) · [ROADMAP.md](../ROADMAP.md) · [PROJECT.md](../PROJECT.md) · [REQUIREMENTS.md](../REQUIREMENTS.md) · [AI_USE.md](AI_USE.md) · [IMPACT.md](../IMPACT.md)
