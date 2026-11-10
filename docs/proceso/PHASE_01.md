# PHASE_01 — Vertical funcional

> **Documento histórico.** Plan de tareas (T0–T14) de la Fase 1, completada. Se conserva como registro del método de trabajo; los pendientes actuales están en [ROADMAP.md](../ROADMAP.md).

> Este documento se lee de forma autónoma: no depende de conversaciones previas.
> Contexto mínimo necesario: [REQUIREMENTS.md](../REQUIREMENTS.md) §2 (reglas) y [CLAUDE.md](../../CLAUDE.md) §2-3 (frontera y reglas de código).

**Objetivo de la fase:** que una solicitud recorra el flujo completo hasta un estado terminal, incluyendo pausa por decisión humana y reanudación tras reiniciar el proceso, verificado por pruebas que corren sin acceso a un modelo externo.

---

## Contexto en 60 segundos

QuoteFlow recibe `customer_id` + texto libre y produce uno de cinco resultados: `NEEDS_CLARIFICATION`, `DRAFT_READY`, `BLOCKED`, `PENDING_APPROVAL`, `REJECTED_BY_POLICY`.

Tres invariantes gobiernan toda esta fase:

1. **El modelo no decide.** Interpreta el texto y redacta prosa; precios, stock, política, routing y aprobaciones viven en `app/domain/` ([ADR-002](../adr/ADR-002-frontera-determinista.md)).
2. **Ningún valor de dominio se codifica.** Todo sale de `app/data/*.json` mediante repositorios.
3. **`Decimal`, nunca `float`,** en cualquier cálculo monetario.

Los datos y los ocho escenarios de referencia ya existen en [`backend/app/data/`](../../backend/app/data).

## Orden de ejecución

```
T0 ──► T1 ──► T2 ─► T3 ─► T4 ─► T5 ─► T6      (dominio determinista, sin LangGraph)
                                        │
                                        ▼
                              T7 ─► T8 ─► T9 ─► T10 ─► T11   (grafo y persistencia)
                                                          │
                                                          ▼
                                              T12 ─► T13 ─► T14   (integración)
```

El dominio se completa y se prueba **antes** de tocar LangGraph. Un grafo construido sobre reglas no verificadas propaga errores difíciles de localizar.

## Tareas

| ID | Tarea | Archivos | Prueba | Definition of Done |
|----|-------|----------|--------|--------------------|
| **T0** ✅ | Inicializar Git y registrar la Fase 0 | `.git/` | — | `git log` muestra un commit con toda la documentación de Fase 0; `git status` limpio |
| **T1** ✅ | Bootstrap del backend | `backend/pyproject.toml`, `backend/app/config.py` | `uv run python -c "import app"` | `uv sync` instala; `ruff` y `mypy` configurados; `Settings` lee `.env` |
| **T2** ✅ | Modelos y enumerados del dominio | `app/domain/models.py`, `app/domain/enums.py` | `tests/unit/test_models.py` | `Outcome`, `ReasonCode`, `Tier`, `DecisionAction` definidos; montos con `Decimal`; `mypy` limpio |
| **T3** ✅ | Repositorios sobre el seed | `app/domain/repositories.py` | `tests/unit/test_repositories.py` | Los 4 repositorios cargan y validan el JSON; `disponible = on_hand − reserved`; SKU inexistente devuelve `None`, no lanza |
| **T4** ✅ | Motor de precios | `app/domain/pricing.py` | `tests/unit/test_pricing.py` | Reproduce AC-01 exacto: 900.00 → 72.00 → **828.00** → IGV 149.04 → 977.04. Redondeo `ROUND_HALF_UP` (RF-06, BR-04) |
| **T5** ✅ | Motor de política | `app/domain/policy.py` | `tests/unit/test_policy.py` | BR-05…BR-09. Precedencia verificada: techo duro domina sobre aprobación; motivos concurrentes se acumulan y se resuelven con una sola decisión |
| **T6** ✅ | Validación y completitud | `app/domain/validation.py` | `tests/unit/test_validation.py` | BR-10…BR-13. Falta cantidad ⇒ `MISSING_QUANTITY`; sede y fecha ausentes **no** bloquean (BR-11) |
| **T7** ✅ | Estado tipado del grafo | `app/graph/state.py` | `tests/unit/test_state.py` | `QuoteState` en Pydantic con todos los campos de `PROJECT.md` §4.2; `mypy` limpio sobre este archivo |
| **T8** ✅ | Frontera del LLM y extractor determinista | `app/llm/base.py`, `app/llm/fake_extractor.py`, `app/llm/prompts.py` | `tests/unit/test_extraction_sanitization.py` | `Protocol` de extractor; el fake resuelve los 8 escenarios; una extracción que trae precio, nivel o aprobación queda saneada (BR-03, ADR-002 §2) |
| **T9** ✅ | Nodos del grafo | `app/graph/nodes.py`, `app/domain/tools.py` | `tests/unit/test_nodes.py` | Los 12 nodos de `PROJECT.md` §4.2, cada uno probado en aislamiento. Las consultas de dominio se exponen como herramientas locales invocadas por los nodos |
| **T10** ✅ | Routing condicional | `app/graph/routing.py` | `tests/unit/test_routing.py` | Los 6 casos de enrutamiento, incluido **fallo recuperable**: error de extracción ⇒ 1 reintento ⇒ `NEEDS_CLARIFICATION` con `EXTRACTION_FAILED` (RF-05) |
| **T11** ✅ | Checkpointer y compilación | `app/graph/checkpointer.py`, `app/graph/build.py` | `tests/integration/test_checkpointer.py` | `AsyncPostgresSaver` con `setup()` en el arranque; el grafo compila e interrumpe en `human_approval` ([ADR-003](../adr/ADR-003-persistencia-checkpointer.md)) |
| **T12** ✅ | Integración: los 8 escenarios | `tests/integration/test_scenarios.py` | ella misma | AC-01…AC-08 en verde con `LLM_MODE=fake`, comparando `outcome` **y** `reason_code` |
| **T13** ✅ | Integración: reanudación durable | `tests/integration/test_interrupt_resume.py` | ella misma | AC-09: interrumpir, **descartar la instancia del grafo y reconstruirla** simulando reinicio, reanudar con el mismo `thread_id`, llegar a `DRAFT_READY` |
| **T14** ✅ | Integración: idempotencia | `tests/integration/test_idempotency.py` | ella misma | AC-10: el mismo `decision_id` dos veces produce un solo efecto y la misma respuesta. AC-11: `REJECT` ⇒ `REJECTED_BY_POLICY` con actor y motivo auditados |

## Definition of Done de la fase

| # | Criterio | Comando de verificación |
|---|----------|-------------------------|
| 1 | Suite completa en verde sin modelo externo | `LLM_MODE=fake uv run pytest` |
| 2 | Reglas de dominio verificadas sin Postgres | `uv run pytest tests/unit` |
| 3 | Tipado limpio donde protege | `uv run mypy app/domain app/graph/state.py` |
| 4 | Estilo consistente | `uv run ruff check . && uv run ruff format --check .` |
| 5 | Cálculo de AC-01 exacto al centavo | Incluido en `tests/unit/test_pricing.py` |
| 6 | Reanudación tras reinicio demostrada | `uv run pytest tests/integration/test_interrupt_resume.py -v` |
| 7 | Evidencia registrada con salida real | `EVIDENCE.md` actualizado en el mismo ciclo |

Un commit atómico por tarea. La fase no se cierra con criterios en rojo: si alguno no se alcanza, se declara como limitación en `EVIDENCE.md` y se refleja en `STATE.md`.

## Decisiones ya tomadas — no reabrir sin ADR

- Precios, stock, política y routing viven en `app/domain/`. El LLM no accede a ellos.
- El umbral de USD 10 000 se evalúa sobre el neto tras descuento y antes de IGV (BR-05).
- Un descuento superior al 20 % es rechazo por política, no excepción aprobable (BR-07).
- Cliente desconocido ⇒ nivel `STANDARD` provisional + revisión humana, no bloqueo (BR-08).
- Un ítem sin stock detiene la solicitud completa; no hay cotización parcial (BR-12, BR-13).

## Riesgos de la fase

| Riesgo | Señal temprana | Respuesta |
|--------|----------------|-----------|
| La extracción real no acierta en los 8 escenarios | T12 falla solo con `LLM_MODE=real` | Ejecutar el ciclo de [LOOP.md](LOOP.md): 3 iteraciones, y si persiste, degradar a `NEEDS_CLARIFICATION` y documentarlo |
| `AsyncPostgresSaver` no reanuda tras reinicio | T13 falla | Verificar que el `thread_id` se persiste junto a la solicitud y no se regenera ([CLAUDE.md](../../CLAUDE.md) §7) |
| Los nodos tienen efectos secundarios antes del `interrupt()` | T14 detecta efecto duplicado | Mover los efectos después de `apply_decision`; el reintento del nodo debe ser inocuo |
| Hay que recortar alcance antes de llegar a T12 | — | T12-T14 son innegociables: sostienen el Definition of Done. Se recorta la Fase 2, no esta |

---

**Relacionados:** [ROADMAP.md](../ROADMAP.md) · [REQUIREMENTS.md](../REQUIREMENTS.md) · [CLAUDE.md](../../CLAUDE.md) · [LOOP.md](LOOP.md)
