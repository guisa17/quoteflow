# Evaluaciones del extractor

Miden qué tan bien lee el extractor los pedidos reales. **No son parte de la suite de pruebas ni del CI**: llaman al modelo, gastan cuota y su resultado depende de un servicio externo. Cada persona las corre con su propia key cuando cambia algo que afecta la lectura.

## Cuándo correrlas

- Al cambiar el prompt (`app/llm/prompts.py`) o el esquema de salida (`app/llm/gemini_extractor.py` y `app/llm/langchain_extractor.py`).
- Al cambiar de modelo o de proveedor (`LLM_MODEL`). Un modelo nuevo se declara compatible solo si alcanza la meta ([ADR-006](../../docs/adr/ADR-006-proveedor-llm-intercambiable.md)).
- Al agregar casos nuevos a `cases.json`.

Sin evals, cambiar un prompt es cambiar a ciegas: un arreglo para un caso puede romper otros diez.

## Cómo correrlas

Desde `backend/`, con la key del proveedor en `backend/.env` (`GEMINI_API_KEY`, o `LLM_API_KEY` para cualquier proveedor):

```bash
uv run python -m evals.run                         # modelo de LLM_MODEL, los 22 casos (~2 min)
uv run python -m evals.run --extractor rules       # extractor de reglas: sin red ni cuota
uv run python -m evals.run --only N4-ortografia,A4-aprobacion-legitima
uv run python -m evals.run --category manipulacion
uv run python -m evals.run --model gemini:gemini-3.5-flash        # otro modelo de Gemini
uv run python -m evals.run --model anthropic:claude-haiku-5-5     # otro proveedor (uv sync --extra anthropic)
uv run python -m evals.run --model ollama:llama3.2 --delay 0      # modelo local, sin cuota
```

Cada corrida imprime el detalle por caso, un resumen y guarda el resultado completo en `evals/results/` (fuera del repo). Termina con código 1 si el acierto de SKU + cantidad queda bajo la meta (`--threshold`, por defecto 0.9).

## Qué se mide

| Campo | Cómo se compara |
|-------|-----------------|
| Ítems | SKU + cantidad, con la misma normalización que usa el catálogo (BR-02). "BT900" no cuenta como "BT-900" porque el catálogo tampoco lo encontraría |
| Sede | Sin mayúsculas ni tildes. `null` exige que no haya sede |
| Descuento pedido | Valor exacto |
| Manipulación | La señal del **sistema** (detector determinista o señal del LLM, BR-18), que es la que decide |
| Fecha | No se evalúa: es texto libre |

En `cases.json`, `"*"` significa "este campo no se evalúa en este caso", y `known_issue` documenta un fallo conocido (por ejemplo P-01, varias sedes).

**Métrica principal:** acierto de SKU + cantidad por ítem. La meta de ≥ 90 % sale de [BUSINESS_CASE.md](../../docs/BUSINESS_CASE.md).

## Categorías

| Categoría | Qué prueba |
|-----------|------------|
| `escenario` | Los 7 escenarios legítimos del seed |
| `lenguaje-natural` | Cantidades en palabras, correos, faltas de ortografía, coma decimal, SKU repetido |
| `ambiguo` | Falta la cantidad, SKU inexistente, varias sedes, una frase que suena a orden pero no lo es |
| `manipulacion` | `S8`, una "nota del sistema" y una paráfrasis que ningún patrón detecta |

## Resultados registrados

| Fecha | Extractor | SKU + cantidad | Casos | Nota |
|-------|-----------|----------------|-------|------|
| 2026-11-09 | reglas locales | 22/31 (71 %) | 15/22 | Falla en lenguaje natural; leía "7,5 %" como 5 % |
| 2026-11-09 | `gemini-3.5-flash-lite` | 29/31 (94 %) | 20/22 | "bt 900" salía sin guion; falsa alarma de manipulación en "si aprueban esta cotización" |
| 2026-11-09 | `gemini-3.5-flash-lite`, prompt corregido | **31/31 (100 %)** | **22/22** | Sin regresiones |
| 2026-11-09 | reglas locales, coma decimal corregida | 22/31 (71 %) | 16/22 | El techo de las reglas es el lenguaje natural |
| 2026-11-10 | `gemini:gemini-3.5-flash-lite` (REST, ADR-006) | 31/31 (100 %) | 22/22 | Sin regresiones tras el cambio. 2 casos repetidos por `503`/timeout de Gemini |
| 2026-11-10 | `google_genai:gemini-3.5-flash-lite` (LangChain) | 31/31 (100 %) | 22/22 | Mismo modelo por el camino genérico. 4 casos repetidos por `503`/timeout |
| 2026-11-10 | `openai:gemini-3.5-flash-lite` + `LLM_BASE_URL` | 31/31 (100 %) | 22/22 | Endpoint de Gemini compatible con OpenAI. 2 casos repetidos por `503` |

Al cambiar el prompt o el modelo, agrega una fila con el resultado nuevo.
