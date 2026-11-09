# REQUIREMENTS — QuoteFlow

Especificación verificable. Cada regla tiene identificador estable (`BR-xx`, `RF-xx`, `RNF-xx`) y se referencia desde el código y las pruebas.

---

## 1. Vocabulario

| Término | Definición operativa |
|---------|----------------------|
| **Solicitud** | `customer_id` + texto libre, registrada por un ejecutivo |
| **Extracción** | Salida estructurada y validada del LLM sobre el texto libre |
| **Línea resuelta** | Ítem extraído mapeado a un SKU real del catálogo, con precio y disponibilidad |
| **Disponible** | `on_hand − reserved` del inventario. Es el único stock cotizable |
| **Neto** | Subtotal − descuento, **antes** de impuestos |
| **Total** | Neto + IGV |
| **Resultado (`outcome`)** | Uno de los cinco estados terminales de la solicitud |
| **`thread_id`** | Identificador de la ejecución en el checkpointer de LangGraph |

## 2. Reglas de negocio

### 2.1 Integridad — el modelo no inventa

| ID | Regla |
|----|-------|
| **BR-01** | El LLM **no puede** producir clientes, productos, precios, stock, descuentos ni aprobaciones. Solo extrae intención del texto y redacta prosa. |
| **BR-02** | Un ítem se resuelve a SKU **solo por coincidencia exacta** con el catálogo (normalizada: mayúsculas, sin espacios ni guiones sobrantes). Sin sustitución por similitud. |
| **BR-03** | Precio unitario, disponibilidad y parámetros de política se leen **exclusivamente** del seed de dominio. Cualquier valor de estas familias presente en la extracción se descarta. |
| **BR-04** | Todo cálculo monetario usa `Decimal` con redondeo `ROUND_HALF_UP` a 2 decimales. Prohibido `float` en el dominio. |

### 2.2 Aprobación y política

| ID | Regla |
|----|-------|
| **BR-05** | Neto > **USD 10 000** ⇒ requiere aprobación humana (`THRESHOLD_EXCEEDED`). El umbral se evalúa sobre el **neto después de descuento y antes de IGV**. |
| **BR-06** | Descuento solicitado > máximo del nivel del cliente ⇒ excepción de política ⇒ requiere aprobación (`DISCOUNT_EXCEPTION`). Máximos: GOLD 12 %, SILVER 8 %, STANDARD 5 %. |
| **BR-07** | Descuento solicitado > **techo duro de 20 %** ⇒ `REJECTED_BY_POLICY`. Ningún humano puede aprobarlo desde el MVP; es un rechazo, no una excepción. |
| **BR-08** | `customer_id` no presente en el registro de clientes ⇒ requiere revisión humana (`UNKNOWN_CUSTOMER`). Se asigna el nivel más conservador (`STANDARD`) para el cálculo provisional. |
| **BR-09** | Precedencia: BR-07 (rechazo) domina sobre cualquier motivo de aprobación. Si concurren varios motivos de aprobación, se registran **todos** y se resuelven con **una sola** decisión humana. |

### 2.3 Completitud e inventario

| ID | Regla |
|----|-------|
| **BR-10** | Información **esencial** para cotizar: al menos una referencia de producto **y** una cantidad entera > 0 por ítem. Falta ⇒ `NEEDS_CLARIFICATION` antes de calcular nada. |
| **BR-11** | Sede, fecha requerida y descuento **no** son esenciales. Si faltan, se registran como "a confirmar" (descuento ausente = 0 %) y la cotización procede. |
| **BR-12** | Ítem con SKU no existente o inactivo ⇒ `BLOCKED` / `UNKNOWN_SKU`. No se cotizan parcialmente los ítems restantes. |
| **BR-13** | Cantidad solicitada **acumulada por SKU** > disponible ⇒ `BLOCKED` / `INSUFFICIENT_STOCK`, indicando disponible real. Repetir un SKU en varias líneas no permite superar el stock. |

### 2.4 Decisión humana

| ID | Regla |
|----|-------|
| **BR-14** | La decisión humana es `APPROVE` \| `REJECT` \| `OBSERVE` (observación sin resolver, mantiene el caso en pausa). |
| **BR-15** | **Idempotencia:** cada decisión lleva `decision_id` único. Reenviar un `decision_id` ya aplicado en el mismo `thread_id`, con la misma acción, no produce efecto adicional y devuelve el estado existente. |
| **BR-16** | Toda decisión queda auditada con `decision_id`, actor, timestamp, motivo y estado previo/posterior. |
| **BR-19** | **Conflicto:** una decisión que contradice lo registrado se reporta y no se aplica: el mismo `decision_id` con otra acción, o un `decision_id` nuevo sobre un caso que no está en pausa. Las decisiones sobre una misma solicitud se serializan, también entre procesos: de dos simultáneas gana exactamente una. |

### 2.5 Seguridad de entrada

| ID | Regla |
|----|-------|
| **BR-17** | El texto del cliente es **entrada no confiable**. Se pasa al LLM como dato delimitado, nunca concatenado a las instrucciones del sistema. |
| **BR-18** | Ninguna instrucción contenida en el texto del cliente puede alterar políticas, umbrales, niveles, routing ni producir aprobación. Un intento detectado se registra en la auditoría y el caso sigue el flujo normal sobre los datos extraídos. |
| **BR-20** | Límites de entrada de la API, tras quitar espacios: `customer_id` 1–64 caracteres, `raw_text` 1–10 000, `decision_id` 1–128, `actor` 1–254, `comment` hasta 2 000. Fuera de esos límites ⇒ `422`, sin ejecutar el grafo. |

## 3. Requisitos funcionales

> RF-01…RF-04 son el contrato entre `frontend/` y `app/api/`. Su forma exacta de intercambio (shapes JSON, tipos, convenciones de serialización) está fijada en [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) — es la fuente de verdad para construir ambos lados en paralelo sin deriva.

| ID | Requisito |
|----|-----------|
| **RF-01** | `POST /requests` — registra solicitud (`customer_id`, `raw_text`), abre `thread_id`, ejecuta el grafo hasta un estado terminal o hasta `interrupt()`. |
| **RF-02** | `GET /requests` — bandeja: id, cliente, resumen, `outcome`, motivo, actualizado. |
| **RF-03** | `GET /requests/{id}` — detalle: extracción, líneas resueltas, cotización, riesgos, auditoría, borrador. |
| **RF-04** | `POST /requests/{id}/decision` — `{decision_id, action, actor, comment}`; reanuda el grafo. Idempotente (BR-15). |
| **RF-05** | Extracción con salida estructurada validada por Pydantic. Esquema inválido ⇒ 1 reintento ⇒ si falla, `NEEDS_CLARIFICATION` con `EXTRACTION_FAILED` registrado. Es el caso **fallo recuperable**: el sistema nunca cotiza sobre una extracción no validada. |
| **RF-05b** | Las consultas de dominio se exponen como herramientas locales en `app/domain/tools.py` (`lookup_customer`, `lookup_product`, `check_availability`, `get_unit_price`, `get_policy`) y las invocan los nodos del grafo, no el modelo. Ver [PROJECT.md](PROJECT.md) §4.2.1. |
| **RF-06** | Cálculo determinista: por línea `subtotal = round(qty × precio, 2)`; `descuento = round(subtotal_total × pct/100, 2)`; `neto = subtotal − descuento`; `IGV = round(neto × 0.18, 2)`; `total = neto + IGV`. |
| **RF-07** | `interrupt()` en `human_approval`, con estado persistido en Postgres. |
| **RF-08** | Auditoría legible: secuencia de nodos ejecutados, transiciones de estado, reglas disparadas, errores y decisiones humanas. |
| **RF-09** | UI: crear solicitud · bandeja con estado · detalle con trazabilidad · aprobar/rechazar/observar · ver borrador. |
| **RF-10** | Modo test sin LLM externo: extractor fake determinista seleccionado por variable de entorno. |

## 4. Requisitos no funcionales

| ID | Requisito |
|----|-----------|
| **RNF-01** | Checkpointer persistente (PostgreSQL). La memoria en proceso solo se admite en pruebas. |
| **RNF-02** | Reanudación durable: reiniciar el backend no pierde solicitudes en `PENDING_APPROVAL`. |
| **RNF-03** | Sin secretos versionados; `.env.example` presente y suficiente. |
| **RNF-04** | `ruff` limpio; `mypy` sin errores en `app/domain` y `app/graph/state.py`. |
| **RNF-05** | Suite completa reproducible offline. |
| **RNF-06** | Errores previsibles (LLM caído, JSON inválido, SKU nulo, BD no disponible) manejados con mensaje accionable, sin traza cruda en la UI. |

## 5. Criterios de aceptación

Cada criterio se verifica con el escenario del seed indicado ([`sample_requests.json`](backend/app/data/sample_requests.json)) y queda registrado en `EVIDENCE.md`.

| ID | Criterio | Escenario | Resultado esperado | Reglas |
|----|----------|-----------|--------------------|--------|
| **AC-01** | Caso estándar dentro de política | `S1` | `DRAFT_READY`, subtotal 900.00, desc. 72.00, neto 828.00, IGV 149.04, total 977.04 | BR-04, BR-06 |
| **AC-02** | Información esencial faltante | `S2` | `NEEDS_CLARIFICATION` / `MISSING_QUANTITY`, sin cotización calculada | BR-10 |
| **AC-03** | Aprobación por monto | `S3` | `PENDING_APPROVAL` / `THRESHOLD_EXCEEDED`, neto 12 900.00 | BR-05 |
| **AC-04** | Aprobación por excepción de descuento | `S4` | `PENDING_APPROVAL` / `DISCOUNT_EXCEPTION` (STANDARD 5 % < 10 %) | BR-06 |
| **AC-05** | Stock insuficiente | `S5` | `BLOCKED` / `INSUFFICIENT_STOCK`, reporta disponible 80 | BR-13 |
| **AC-06** | SKU inexistente | `S6` | `BLOCKED` / `UNKNOWN_SKU`, sin sustitución | BR-02, BR-12 |
| **AC-07** | Cliente desconocido | `S7` | `PENDING_APPROVAL` / `UNKNOWN_CUSTOMER` | BR-08 |
| **AC-08** | Inyección de prompt | `S8` | `REJECTED_BY_POLICY` / `DISCOUNT_ABOVE_HARD_CEILING`; **nunca** aprobado automáticamente | BR-07, BR-17, BR-18 |
| **AC-09** | Reanudación durable | `S3` | Interrumpir, **reiniciar el backend**, aprobar ⇒ el caso continúa a `DRAFT_READY` | RNF-02 |
| **AC-10** | Idempotencia | `S3` | Enviar dos veces el mismo `decision_id` ⇒ un solo efecto, misma respuesta | BR-15 |
| **AC-11** | Rechazo humano | `S4` | `REJECT` ⇒ `REJECTED_BY_POLICY` (mismo estado terminal que un rechazo automático: "rechazado o escalado por política" es un solo resultado), con motivo y actor auditados | BR-14, BR-16 |
| **AC-12** | Suite offline | — | `pytest` en verde sin credenciales de LLM | RF-10, RNF-05 |
| **AC-13** | Stock acumulado | — | 80 + 1 `RP-300` con 80 disponibles ⇒ `BLOCKED` / `INSUFFICIENT_STOCK`, solicitado 81 | BR-13 |
| **AC-14** | Decisiones en conflicto | `S3` | Mismo `decision_id` con otra acción, decisión nueva sobre caso cerrado o dos simultáneas ⇒ `409` para la que no se aplica, con el caso intacto | BR-15, BR-19 |
| **AC-15** | Límites de entrada | — | Actor o `decision_id` vacío, o texto de más de 10 000 caracteres ⇒ `422` | BR-20 |
| **AC-16** | Corte de Postgres | — | Con Postgres detenido, `/health` ⇒ `503`; al volver, la API responde sin reiniciar el backend | RNF-06 |

## 6. Trazabilidad de datos

Seed versionado en [`backend/app/data/`](backend/app/data/) — [ADR-001](docs/adr/ADR-001-datos-ficticios-propios.md):

| Archivo | Contenido |
|---------|-----------|
| `customers.json` | 3 clientes: `FER-1001` GOLD · `FER-1002` SILVER · `FER-1003` STANDARD |
| `products.json` | 6 SKU de EPP con precio de lista y lead time |
| `inventory.json` | `on_hand` / `reserved` por SKU y almacén |
| `policies.json` | Máximos por nivel, techo duro, umbral de aprobación, IGV |
| `sample_requests.json` | 8 escenarios con `expected_outcome`, base de AC-01…AC-08 |

---

**Relacionados:** [PROJECT.md](PROJECT.md) · [BUSINESS_CASE.md](BUSINESS_CASE.md) · [ADR-002](docs/adr/ADR-002-frontera-determinista.md)
