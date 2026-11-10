# ADR-006 — Proveedor de LLM intercambiable con `LLM_MODEL=proveedor:modelo`

- **Estado:** Aceptada
- **Fecha:** 2026-11-10
- **Decisor:** Guillermo Salcedo
- **Afecta a:** `app/llm/factory.py`, `app/llm/langchain_extractor.py`, `app/llm/base.py`, `app/graph/build.py`, `app/config.py`, `evals/run.py`, `pyproject.toml`, `.env.example`
- **Relacionada con:** [ADR-002](ADR-002-frontera-determinista.md) (frontera determinista), [ADR-004](ADR-004-extractor-gemini-con-respaldo.md) (Gemini con respaldo)

---

## Contexto

ADR-004 conectó un solo proveedor, Gemini, porque su plan gratuito permitía una demo sin costo. El resto del sistema ya era independiente del proveedor: el grafo solo conoce el `Extractor` Protocol, y la frontera de ADR-002 (validar contra `Extraction` con `extra="ignore"`) no depende de quién produjo el JSON.

Lo que faltaba era poder elegir otro modelo sin escribir código. Las razones son prácticas:

1. **Quien clona el repo tiene la key que tiene.** Una empresa suele tener contrato con un solo proveedor (OpenAI, Anthropic, Azure, Bedrock) y no puede usar otro.
2. **Datos que no deben salir de la red.** Con datos reales, un modelo local (Ollama, vLLM) puede ser la única opción aceptable.
3. **Comparar modelos con la misma prueba.** Las evals solo tienen sentido si se puede cambiar el modelo y medir de nuevo.

## Decisión

**Una sola variable, `LLM_MODEL=proveedor:modelo`. Gemini se mantiene por REST y cualquier otro proveedor pasa por `init_chat_model` de LangChain.**

| Aspecto | Decisión |
|---------|----------|
| Configuración | `LLM_MODEL=proveedor:modelo`, la convención de LangChain, LiteLLM y Pydantic AI. `LLM_API_KEY` para la key, `LLM_BASE_URL` para servidores compatibles con OpenAI o un Ollama remoto |
| `gemini:<modelo>` o vacío | `GeminiExtractor`, igual que en ADR-004: es el camino medido y no suma dependencias |
| Cualquier otro proveedor | `LangChainExtractor`: `init_chat_model` crea el cliente y `with_structured_output` fuerza el JSON Schema de extracción con el mecanismo que el proveedor soporte |
| Paquetes | `langchain` es dependencia base; cada proveedor es un extra opcional (`uv sync --extra anthropic`, `openai`, `google`, `ollama`) |
| Errores | Los mismos dos del contrato, para todos los proveedores: cuota, credenciales, red, timeout y 5xx son `ProviderUnavailable` (respaldo con reglas); un 4xx distinto o una salida fuera de esquema es `ExtractionError` (reintento de RF-05) |
| Reintentos | `max_retries=0` en el SDK. El grafo ya reintenta una vez; los reintentos internos retrasarían el respaldo cuando el proveedor está caído |
| Configuración imposible | Proveedor desconocido, paquete ausente o `LLM_MODEL` sin `proveedor:` detienen el arranque con un mensaje que dice qué hacer. Una key faltante no: se comporta como Gemini sin key, con respaldo visible |

Reglas derivadas:

1. **El prompt, el esquema y la validación son los mismos para todos.** Cambiar de proveedor no cambia qué campos puede producir el modelo ni cómo se descartan los de dominio.
2. **Un modelo nuevo se declara compatible solo después de pasar las evals** (≥ 90 % de SKU + cantidad, [BUSINESS_CASE.md](../BUSINESS_CASE.md)). Que la llamada funcione no basta: no todos los modelos siguen igual un esquema.
3. **La suite sigue sin red y sin extras.** El cliente de chat se reemplaza por un doble en `tests/unit/test_llm_providers.py`; el CI no instala ningún paquete de proveedor.

## Alternativas consideradas

| Alternativa | Descartada porque |
|-------------|-------------------|
| Un extractor escrito a mano por proveedor | Cada uno repite cliente, esquema y clasificación de errores. Con dos proveedores ya es duplicación; con cinco es mantenimiento |
| Solo el endpoint compatible con OpenAI (`base_url` + `api_key`) | Cubre a casi todos, Gemini incluido, sin dependencias. Pero la compatibilidad de la salida estructurada varía entre servidores, y la API nativa de Anthropic no se usa así. Se conserva como un caso más: `openai:<modelo>` con `LLM_BASE_URL` |
| LiteLLM | Mismo alcance, pero suma una abstracción paralela a LangChain en un proyecto que ya usa LangGraph y LangSmith. LangChain registra la llamada en LangSmith con proveedor, modelo y tokens sin código extra |
| Migrar también Gemini a LangChain | Funciona (se midió abajo), pero cambiaría el camino medido en ADR-004, el nombre de las trazas y sumaría un paquete por defecto. No hay beneficio que lo justifique |
| Variables por proveedor (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`...) | `pydantic-settings` no copia `.env` a `os.environ`, así que los SDK no las verían (el mismo problema que tenía LangSmith, E-12). Una key explícita es más simple de documentar |

## Consecuencias

**Positivas**

- Cualquiera de los proveedores de `init_chat_model` (Anthropic, OpenAI, Azure, Bedrock, Mistral, Groq, DeepSeek, OpenRouter, Ollama...) se usa cambiando dos variables.
- Las evals comparan modelos con la misma prueba: `uv run python -m evals.run --model proveedor:modelo`.
- Un modelo local permite usar el sistema sin enviar texto de clientes a terceros.

**Negativas / límites asumidos**

- `langchain` entra como dependencia base, aunque Gemini no la use.
- La clasificación de errores lee el código HTTP que expone cada SDK (`status_code`, `code` o `response.status_code`). Un SDK que no lo exponga cae en `ProviderUnavailable`, que es el lado seguro: respaldo visible.
- Solo Gemini está medido con las evals. Los demás proveedores están probados con dobles y quedan "soportados, no medidos" hasta que alguien corra las evals con su key.

## Verificación

- `tests/unit/test_llm_providers.py`: formato de `LLM_MODEL`, arranque que falla ante una configuración imposible, key faltante con respaldo, frontera del modelo (campos de dominio descartados, `source` fijado por el extractor, texto del cliente en su turno), clasificación de errores y timeout.
- Evals con la key de Gemini por los tres caminos, en [evals/README.md](../../backend/evals/README.md#resultados-registrados):

| Camino | `LLM_MODEL` | SKU + cantidad | Casos |
|--------|-------------|----------------|-------|
| REST nativo (ADR-004) | `gemini:gemini-3.5-flash-lite` | 31/31 (100 %) | 22/22 |
| LangChain, paquete de Google | `google_genai:gemini-3.5-flash-lite` | 31/31 (100 %) | 22/22 |
| LangChain, endpoint compatible con OpenAI | `openai:gemini-3.5-flash-lite` + `LLM_BASE_URL` | 31/31 (100 %) | 22/22 |

En la primera pasada, Gemini devolvió `503` o superó los 20 s en 2, 4 y 2 casos de cada camino, el nativo incluido. Ningún caso respondido salió mal leído. Esos casos se repitieron con `--only` y pasaron. Que el error se clasificara como `ProviderUnavailable` en los tres caminos es, en sí, parte de lo verificado.

- De punta a punta: backend con `LLM_MODE=real` y `LLM_MODEL=google_genai:gemini-3.5-flash-lite`. "Dos docenas de cascos hx 200" terminó en `DRAFT_READY` con `HX-200 × 24`, y la auditoría registra `1 item(s) extraído(s) con gemini-3.5-flash-lite`.
- Arranque con configuración imposible: `LLM_MODEL=claude-sonnet-5` (sin proveedor), `inventado:x` y `groq:...` sin paquete detienen `uvicorn` con `LLMConfigError` y el mensaje de qué corregir.
- Sin medir con evals: Anthropic, OpenAI y Ollama (no había keys ni Ollama en la máquina de verificación).
