# ADR-002 — Frontera determinista: el LLM interpreta y redacta; nunca decide

- **Estado:** Aceptada · enmendada el 2026-11-09 (ver al final)
- **Fecha:** 2026-08-04
- **Decisor:** Guillermo Salcedo
- **Afecta a:** arquitectura del grafo, `app/domain`, `app/llm`, estrategia de pruebas, nivel de autonomía
- **Ampliada por:** [ADR-004](ADR-004-extractor-gemini-con-respaldo.md) (extractor real y respaldo), [ADR-005](ADR-005-manipulacion-a-revision-humana.md) (manipulación a revisión humana), [ADR-006](ADR-006-proveedor-llm-intercambiable.md) (proveedor intercambiable, misma frontera)

---

## Contexto

Dos restricciones, juntas, definen la arquitectura entera:

> El modelo no puede inventar clientes, productos, precios, stock, descuentos ni aprobaciones.
> Interpretación y redacción pueden apoyarse en un LLM; precios, stock, políticas y cálculos deben vivir en funciones del dominio.

A esto se suma que el texto del cliente es **entrada no confiable**: puede contener instrucciones que intenten alterar políticas o forzar una aprobación.

El enfoque habitual en un sistema agéntico consiste en dar al modelo herramientas de consulta y dejar que razone hasta la respuesta. Ese enfoque produce sistemas difíciles de auditar: ante la misma solicitud, dos ejecuciones pueden diferir, y no existe una línea de código que explique por qué una cotización recibió 8 % de descuento.

## Decisión

**El LLM ocupa únicamente los dos extremos del flujo; el centro es 100 % determinista.**

| Etapa | Quién ejecuta | Salida |
|-------|---------------|--------|
| Interpretar texto libre | LLM, con salida estructurada validada por Pydantic | `Extraction` (ítems, cantidades, sede, fecha, descuento solicitado) |
| Resolver cliente, catálogo, inventario | **Funciones deterministas** | Líneas resueltas o bloqueo |
| Calcular precios, descuento y totales | **Funciones deterministas** (`Decimal`) | `Quote` |
| Evaluar política y enrutar | **Funciones deterministas** | `outcome` + motivos |
| Aprobar / rechazar | **Humano** | `HumanDecision` |
| Redactar borrador | LLM (o plantilla determinista) | Texto |

Reglas de frontera derivadas:

1. **El LLM no tiene herramientas de escritura ni de decisión.** No accede a inventario ni a política; solo lee el texto del cliente.
2. **La extracción se sanea antes de usarse.** Cualquier campo de la extracción que pertenezca a una familia de datos de dominio (precio, stock, nivel del cliente, aprobación) se **descarta**, aunque el modelo lo haya producido. El nivel del cliente sale del padrón, no de "somos clientes Gold".
3. **El routing nunca depende de texto libre del modelo.** Depende de comparaciones sobre valores tipados.
4. **El texto del cliente se pasa como dato delimitado**, jamás concatenado a las instrucciones del sistema.
5. **La redacción no puede introducir cifras.** El borrador se construye sobre los valores ya calculados; en modo test se genera con plantilla determinista.

## Alternativas consideradas

| Alternativa | Descartada porque |
|-------------|-------------------|
| Agente ReAct con herramientas de dominio y decisión libre | No auditable ni reproducible. Imposible garantizar BR-01 o el umbral de USD 10 000; el modelo puede "razonar" que 10 400 es aproximadamente 10 000 |
| LLM calcula y el dominio solo verifica a posteriori | Duplica la lógica y deja al modelo definiendo el resultado por defecto. Si la verificación falla, no hay respuesta que dar |
| Sin LLM: parser por reglas sobre el texto | Frágil ante la variedad real del lenguaje comercial — precisamente el problema que justifica el proyecto |
| LLM también decide el routing con salida estructurada (enum) | Aparentemente seguro, pero mueve la política al prompt: cambiar un umbral pasaría a ser un cambio de prompt no testeable |

## Consecuencias

**Positivas**

- El sistema es **explicable por construcción**: toda cifra tiene una función de dominio detrás y toda decisión, una regla identificada (`BR-xx`).
- Las pruebas de reglas, routing e idempotencia corren **sin LLM**, cumpliendo el requisito de suite offline.
- La inyección de prompt queda acotada por diseño: en el peor caso corrompe la *extracción* (ítems o cantidades), nunca el precio, la política ni la aprobación. El escenario `S8` lo demuestra.
- Cambiar una política es editar `policies.json`; no requiere reentrenar, reescribir prompts ni tocar el grafo.

**Negativas / límites asumidos**

- Se pierde flexibilidad: casos no previstos (permutas, kits, cotización parcial) no se resuelven "razonando", terminan en aclaración o bloqueo. Es el comportamiento deseado para el nivel de autonomía 2, pero **eleva la tasa de falsos bloqueos** — por eso es métrica de guardia con techo de 10 % en el business case.
- La calidad del sistema queda acotada por la calidad de la extracción. Es el punto único de fallo aceptado, y por eso se mide aparte (≥ 90 % de acierto en SKU + cantidad).
- Requiere más código de dominio que una solución basada en un agente con herramientas libres. A cambio, ese código es la parte verificable del sistema y la que sostiene los criterios de aceptación.

## Verificación

- `tests/unit/test_pricing.py`, `test_policy.py` — reglas sin LLM.
- `tests/unit/test_extraction_sanitization.py` — una extracción que trae precio/nivel/aprobación es saneada.
- `tests/integration/test_scenarios.py` — los 8 escenarios del seed con extractor fake.
- `tests/integration/test_scenarios.py` y `tests/integration/test_api.py` — `S8` nunca produce una aprobación.

## Enmiendas

El texto de arriba se conserva tal como se aceptó. Estas notas registran en qué difiere la implementación y por qué.

**2026-11-09 — La redacción es siempre una plantilla determinista.** La tabla de la decisión dejaba abierta la redacción del borrador a "LLM (o plantilla determinista)". Lo construido usa la plantilla en todos los modos (`compose_draft` en `app/graph/nodes.py`): el LLM solo interpreta el texto. No cambia la decisión, la acota. Una redacción con LLM sería una extensión futura y tendría que respetar la regla 5.

**2026-11-09 — El parser de reglas vuelve, pero solo como respaldo.** La tabla de alternativas descarta un parser de reglas como solución principal, y eso se mantiene. [ADR-004](ADR-004-extractor-gemini-con-respaldo.md) lo usa únicamente cuando el proveedor del LLM no responde, y siempre de forma visible.

**2026-11-09 — Verificación corregida.** Esta sección citaba `tests/integration/test_prompt_injection.py`, un archivo que nunca existió; `S8` se prueba en `test_scenarios.py` y `test_api.py`.
