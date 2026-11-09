# REFERENCES — Referencias consultadas y dónde se aplicaron

Esta tabla registra **qué se tomó de cada referencia y dónde aterrizó**.

---

## Técnico — LangGraph y agentes

| Referencia | Qué se aplicó | Dónde |
|------------|---------------|-------|
| **LangGraph overview** | Modelo de `StateGraph` con estado tipado y rutas condicionales | [PROJECT.md](../PROJECT.md) §4.2 |
| **Thinking in LangGraph** | Traducción del proceso comercial a 12 nodos con responsabilidad única | [PROJECT.md](../PROJECT.md) §4.2 · [PHASE_01.md](../PHASE_01.md) T9-T10 |
| **Persistence** | `AsyncPostgresSaver`, `setup()` en el arranque, `thread_id` persistido | [ADR-003](adr/ADR-003-persistencia-checkpointer.md) |
| **Interrupts** | `interrupt()` en `human_approval`; el nodo se re-ejecuta al reanudar, de donde sale el requisito de idempotencia | [ADR-003](adr/ADR-003-persistencia-checkpointer.md) · [REQUIREMENTS.md](../REQUIREMENTS.md) BR-15 |
| **Testing LangGraph** | Nodos probados en aislamiento; grafo completo en integración; base de datos solo donde hace falta | [PHASE_01.md](../PHASE_01.md) T12-T14 |

## Negocio — valor, usuario y riesgo

| Referencia | Qué se aplicó | Dónde |
|------------|---------------|-------|
| **A practical guide to building AI agents** — OpenAI | Disparadores de human-in-the-loop por *acción de alto riesgo* (monto) y por *excepción* (descuento fuera de política); guardrails en capas antes que un agente con criterio libre | [REQUIREMENTS.md](../REQUIREMENTS.md) BR-05, BR-06 · [ADR-002](adr/ADR-002-frontera-determinista.md) |
| **People + AI Guidebook** — Google PAIR | Comunicar el porqué, no solo el resultado: el detalle de la solicitud muestra qué se extrajo y qué regla se aplicó junto al borrador. Mitiga el sesgo de automatización | [BUSINESS_CASE.md](../BUSINESS_CASE.md) §6 · [ROADMAP.md](../ROADMAP.md) Fase 2 |
| **Value Proposition Canvas** — Strategyzer | Estructura usuario → proceso actual → dolores → hipótesis de valor | [BUSINESS_CASE.md](../BUSINESS_CASE.md) §1-3 |
| **NIST AI Risk Management Framework** | Las cuatro funciones se reparten así: **Govern** en las reglas de [CLAUDE.md](../CLAUDE.md); **Map** en la tabla de riesgos; **Measure** en las métricas de guardia asimétricas; **Manage** en la condición de corte del piloto | [BUSINESS_CASE.md](../BUSINESS_CASE.md) §5-6, §8 |

## Método — contexto, loops y desarrollo asistido

| Referencia | Qué se aplicó | Dónde |
|------------|---------------|-------|
| **open-gsd/gsd-core** | Prácticas adoptadas: ciclo por fases, contexto fresco por fase, plan legible de forma autónoma. **La herramienta no se instaló** | [AI_USE.md](../AI_USE.md) §2 |
| **Loop Engineering** — Addy Osmani | Un ciclo acotado con objetivo, worker, verifier, presupuesto, condición de salida y condición de bloqueo | [LOOP.md](../LOOP.md) |
| **Claude Code best practices** | Instrucciones persistentes cargadas en cada sesión; planificación antes de ejecutar; verificación con comandos, no con criterio | [CLAUDE.md](../CLAUDE.md) |
| **Codex best practices / AGENTS.md** | Convención de instrucciones persistentes por repositorio. Se eligió `CLAUDE.md` como archivo real por el entorno usado; [`AGENTS.md`](../AGENTS.md) queda como puntero | [CLAUDE.md](../CLAUDE.md) |
| **Graphify** | Generado con la herramienta real (`graphifyy`, extracción de código local vía tree-sitter, sin costo de API) | [docs/graphify/GRAPH_REPORT.md](graphify/GRAPH_REPORT.md), contrastado en [IMPACT.md](../IMPACT.md) §3 |

---

## Nota sobre lo no adoptado

- **`gsd-core` como herramienta instalada.** Genera su propia estructura de artefactos, su fase de ejecución usa oleadas paralelas, y el problema que resuelve —degradación de contexto en proyectos extensos y multi-sesión— no se presenta en un repositorio de esta escala. Detalle en [AI_USE.md](../AI_USE.md) §2.
- **Ejecución con agentes en paralelo como objetivo.** La cantidad de agentes no es un objetivo. Los módulos del dominio están acoplados por un mismo estado tipado, de modo que paralelizarlos produciría colisiones sin ganancia de velocidad.
