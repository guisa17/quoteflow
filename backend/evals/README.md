# Evaluaciones del extractor

Miden qué tan bien lee el extractor los pedidos reales. **No son parte de la suite de pruebas ni del CI**: llaman al modelo, gastan cuota y su resultado depende de un servicio externo. Cada persona las corre con su propia key cuando cambia algo que afecta la lectura.

## Cuándo correrlas

- Al cambiar el prompt (`app/llm/prompts.py`) o el esquema de salida (`app/llm/gemini_extractor.py`).
- Al cambiar de modelo (`GEMINI_MODEL`) o de proveedor.
- Al agregar casos nuevos a `cases.json`.

Sin evals, cambiar un prompt es cambiar a ciegas: un arreglo para un caso puede romper otros diez.

## Cómo correrlas

Desde `backend/`, con `GEMINI_API_KEY` en `backend/.env`:

```bash
uv run python -m evals.run                         # Gemini, los 22 casos (~1 min, 22 llamadas)
uv run python -m evals.run --extractor rules       # extractor de reglas: sin red ni cuota
uv run python -m evals.run --only N4-ortografia,A4-aprobacion-legitima
uv run python -m evals.run --category manipulacion
uv run python -m evals.run --model gemini-3.5-flash  # comparar otro modelo
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

Al cambiar el prompt o el modelo, agrega una fila con el resultado nuevo.
