# ADR-004 — Extractor real con Gemini y respaldo explícito al extractor de reglas

- **Estado:** Aceptada
- **Fecha:** 2026-11-09
- **Decisor:** Guillermo Salcedo
- **Afecta a:** `app/llm/gemini_extractor.py`, `app/llm/fallback.py`, `app/graph/build.py`, `app/config.py`, `Extraction.source`, `.env.example`
- **Relacionada con:** [ADR-002](ADR-002-frontera-determinista.md) (frontera determinista)

---

## Contexto

Hasta la Fase 3 el sistema solo leía el texto con `FakeExtractor`, un extractor de reglas pensado como doble de pruebas. Resuelve los 8 escenarios, pero no entiende lenguaje real: "dos docenas de cascos" o "quince arneses" quedan sin cantidad. ADR-002 ya descartaba un parser de reglas como solución principal por eso mismo.

Hacía falta un LLM real con tres condiciones:

1. **Costo cero para una demo**, sin tarjeta de crédito.
2. **Salida estructurada forzada**, para que la frontera de ADR-002 (Pydantic con `extra="ignore"`) reciba siempre el mismo esquema.
3. **Que un proveedor caído no rompa la demo.** Un plan gratuito tiene cuota diaria baja y picos de saturación.

## Decisión

**Gemini por su API REST, con salida JSON forzada por esquema y respaldo explícito al extractor de reglas.**

| Aspecto | Decisión |
|---------|----------|
| Proveedor | Gemini, plan gratuito de Google AI Studio |
| Cliente | `httpx` contra la API REST, sin SDK del proveedor |
| Modelo | `gemini-3.5-flash-lite`, configurable con `GEMINI_MODEL` |
| Salida | `responseMimeType: application/json` + `responseSchema` con solo los campos de `Extraction`; temperatura 0 |
| Fallo del proveedor (sin key, 429, 401/403, 5xx, red, timeout) | `ProviderUnavailable` → se lee con el extractor de reglas |
| Salida fuera de esquema | `ExtractionError` → reintento y degradación de RF-05, **sin** respaldo |
| Procedencia | `Extraction.source` = versión del modelo o `"reglas locales (respaldo: <motivo>)"`; visible en el folio y en la auditoría |

Reglas derivadas:

1. **El respaldo nunca es silencioso.** Si se usa el extractor de reglas, el folio lo dice en ámbar y la auditoría registra el motivo.
2. **Solo el fallo del proveedor activa el respaldo.** Una respuesta que no valida contra el esquema sí dice algo del texto (es ambiguo o el modelo se equivocó), y ese caso ya tiene su camino en RF-05.
3. **El modelo no puede escribir su propia procedencia.** `source` se fija después de validar.
4. **Las pruebas no llaman al proveedor.** Se simulan sus respuestas con `httpx.MockTransport`; la suite sigue sin red (RF-10).

### Por qué este modelo

Se probaron los modelos Flash disponibles para la key (noviembre 2026):

| Modelo | Resultado |
|--------|-----------|
| `gemini-flash-latest` (alias) | Sin respuesta en 60 s |
| `gemini-3.8-flash` | Sin respuesta en 60 s |
| `gemini-2.5-flash` | 404: no disponible para cuentas nuevas |
| `gemini-3.5-flash-lite` | ~2 s, extracción correcta en los 8 escenarios y en lenguaje natural |

Se fija un nombre concreto en vez del alias: un alias cambia de modelo sin aviso, y eso invalida cualquier medición anterior. Para una extracción corta y estructurada, un modelo Lite basta.

## Alternativas consideradas

| Alternativa | Descartada porque |
|-------------|-------------------|
| Claude (Anthropic), previsto en el diseño original | No tiene plan gratuito para la API. Queda como segundo proveedor: `LLM_PROVIDER=anthropic` está reservado |
| SDK oficial de Gemini | Una dependencia más para una sola llamada HTTP; la API REST es estable y `httpx` ya estaba en el proyecto |
| Sin respaldo: si el proveedor falla, `NEEDS_CLARIFICATION` | Con una cuota gratuita, la demo fallaría justo cuando alguien la prueba. Además confunde "el proveedor no respondió" con "el texto es ambiguo" |
| Respaldo silencioso | Esconde una degradación de calidad: el operador revisaría con menos cuidado una lectura que vino de reglas |
| Respaldo también ante salida fuera de esquema | Taparía errores del modelo o del prompt que deben verse y medirse |

## Consecuencias

**Positivas**

- El sistema entiende pedidos reales: cantidades en palabras, varios productos, estilo de correo.
- La demo no se rompe por cuota o saturación, y el usuario sabe cuándo leyó un modelo y cuándo reglas.
- Cambiar de proveedor es implementar el mismo `Extractor` Protocol; el resto del grafo no cambia.

**Negativas / límites asumidos**

- En el plan gratuito, Google puede usar lo enviado para mejorar sus productos. Se acepta porque todos los datos son ficticios ([ADR-001](ADR-001-datos-ficticios-propios.md)); con datos reales habría que pasar a un plan de pago.
- La calidad de la extracción depende de un modelo que puede cambiar o retirarse; por eso se fija el nombre y se mide con evaluaciones aparte de la suite.
- El extractor de reglas sigue siendo rígido: en respaldo, un pedido en lenguaje natural puede terminar en aclaración.

## Verificación

- `tests/unit/test_gemini_extractor.py` — esquema, BR-17, descarte de campos de dominio, errores del proveedor, respaldo, y que una salida fuera de esquema no active el respaldo.
- Prueba en vivo con la key: los 8 escenarios y casos en lenguaje natural ("dos docenas" = 24). Ver [ROADMAP.md](../ROADMAP.md), Fase 4.
