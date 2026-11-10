# API_CONTRACT — Contrato de RF-01…RF-04

Fuente de verdad del formato de intercambio entre `frontend/` y `app/api/`. Existe para que ambos se construyan en paralelo sin deriva: ninguno de los dos inventa la forma del otro lado.

**Regla de precedencia:** si el frontend y `app/api/` alguna vez discrepan sobre una forma, este documento decide, no el código de ninguno de los dos. Se corrige el que se desvió.

---

## Convenciones

- Todo monto monetario viaja como **string decimal** (`"828.00"`), nunca como `number`. Serializar `Decimal` como float arriesga precisión en el borde de red — la misma razón de BR-04, aplicada al contrato HTTP. El frontend formatea para mostrar; no hace aritmética con estos valores.
- Cantidades (`quantity`) sí son `number` (enteros).
- Fechas van en ISO 8601 (`"2026-08-04T14:30:00Z"`).
- Los enums (`Outcome`, `ReasonCode`, `DecisionAction`) viajan como el string exacto definido en `app/domain/enums.py` — mismo valor en ambos lados, cero traducción.

## Tipos compartidos

```typescript
type Outcome =
  | "NEEDS_CLARIFICATION" | "DRAFT_READY" | "BLOCKED"
  | "PENDING_APPROVAL" | "REJECTED_BY_POLICY"

type ReasonCode =
  | "MISSING_PRODUCT_REFERENCE" | "MISSING_QUANTITY" | "UNKNOWN_SKU"
  | "INSUFFICIENT_STOCK" | "THRESHOLD_EXCEEDED" | "DISCOUNT_EXCEPTION"
  | "UNKNOWN_CUSTOMER" | "DISCOUNT_ABOVE_HARD_CEILING" | "EXTRACTION_FAILED"
  | "SUSPECTED_MANIPULATION"             // BR-18: el texto intenta dar ordenes al sistema

type DecisionAction = "APPROVE" | "REJECT" | "OBSERVE"

interface ApprovalReason {
  reason_code: ReasonCode
  detail: string
}

interface ExtractedLineItem {
  product_reference: string
  quantity: number | null
}

interface Extraction {
  items: ExtractedLineItem[]
  site: string | null
  requested_date: string | null
  requested_discount_pct: string | null   // string decimal o null
  source: string | null                   // quien leyo el texto: modelo o "reglas locales (respaldo: ...)"
}

interface QuoteLine {
  sku: string
  product_name: string
  quantity: number
  unit_price: string        // string decimal
  line_subtotal: string     // string decimal
}

interface Quote {
  lines: QuoteLine[]
  subtotal: string
  discount_pct: string
  discount_amount: string
  net: string
  tax_amount: string
  total: string
  currency: string
}

interface AuditEvent {
  node: string           // nombre del nodo del grafo que lo genero
  timestamp: string
  note: string
  reason_code: ReasonCode | null  // presente si el evento registra un motivo (p. ej. SUSPECTED_MANIPULATION)
}

interface HumanDecision {
  decision_id: string
  action: DecisionAction
  actor: string
  comment: string | null
  timestamp: string
}
```

## RF-01 · `POST /requests`

Registra la solicitud y corre el grafo hasta un estado terminal o hasta `interrupt()`. Es **síncrona**: cuando responde, `outcome` ya está resuelto (nunca `null`).

**Request:**
```typescript
interface CreateRequestBody {
  customer_id: string   // 1-64 caracteres tras quitar espacios (BR-20)
  raw_text: string      // 1-10 000 caracteres tras quitar espacios (BR-20)
}
```

**Response `201`:** el mismo shape que `RequestDetail` (ver RF-03) — no hay una forma reducida separada; el detalle completo ya está disponible en cuanto se crea.

**`422`** si el cuerpo no cumple los límites.

## RF-02 · `GET /requests`

Bandeja de solicitudes.

**Response `200`:**
```typescript
interface RequestSummary {
  id: string
  customer_id: string
  customer_name: string       // "" si el cliente es desconocido (BR-08)
  summary: string             // ej. "20 x HX-200"
  outcome: Outcome
  reason_code: ReasonCode | null   // el motivo principal si no es DRAFT_READY
  updated_at: string
}

type RequestListResponse = RequestSummary[]
```

## RF-03 · `GET /requests/{id}`

Detalle completo con trazabilidad.

**Response `200`:**
```typescript
interface RequestDetail {
  id: string
  thread_id: string
  customer_id: string
  customer_name: string
  raw_text: string
  outcome: Outcome

  extraction: Extraction | null        // null si fallo la extraccion (EXTRACTION_FAILED)
  quote: Quote | null                  // null si el outcome no llego a calcular (NEEDS_CLARIFICATION, BLOCKED)
  approval_reasons: ApprovalReason[]   // BR-09: puede haber varios, concurrentes
  rejection_reason: ApprovalReason | null   // BR-07: presente solo si outcome = REJECTED_BY_POLICY
  blocking_reason: ApprovalReason | null    // presente solo si outcome = BLOCKED o NEEDS_CLARIFICATION

  audit_trail: AuditEvent[]
  human_decision: HumanDecision | null      // null hasta que alguien decide
  draft_text: string | null                 // solo si outcome = DRAFT_READY

  created_at: string
  updated_at: string
}
```

**`404`** si el id no existe.

## RF-04 · `POST /requests/{id}/decision`

Aprobar, rechazar u observar. Idempotente por `decision_id` (BR-15): reenviar la misma decisión (mismo `decision_id` y misma `action`) sobre el mismo `id` devuelve `200` con el mismo resultado, sin efecto adicional.

**Request:**
```typescript
interface DecisionBody {
  decision_id: string     // 1-128 caracteres. El frontend usa un UUID por intento y lo conserva solo al reintentar la misma accion
  action: DecisionAction
  actor: string           // 1-254 caracteres tras quitar espacios
  comment?: string        // hasta 2 000 caracteres
}
```

**Response `200`:** el `RequestDetail` actualizado (mismo shape que RF-03), con `human_decision` poblado y `outcome` avanzado si la decision resolvio el caso.

**`404`** si el id no existe. **`409`** si la decisión contradice lo registrado y no se aplicó (BR-19): el mismo `decision_id` con otra `action`, o un `decision_id` nuevo sobre un caso que no está en pausa. **`422`** si `action` no es un valor valido o el cuerpo no cumple los límites (BR-20).

## `GET /health`

**`200`** con `{"status": "ok"}` si responden las dos conexiones a Postgres que usa la API. **`503`** con `{"status": "unavailable"}` en cualquier otro caso.

## Errores

Todo error de negocio (no de validación de esquema) responde con:

```typescript
interface ApiError {
  detail: string
}
```

En el status HTTP correspondiente (`404`, `409`, `422`, `500`, `503`). `503` indica que la base de datos no está disponible (RNF-06). El frontend no debe parsear el texto de `detail` para tomar decisiones — es para mostrarlo al usuario, no para lógica. Un `422` de validación de esquema trae `detail` como lista de errores, según el formato de FastAPI.

---

**Relacionados:** [REQUIREMENTS.md §3](../REQUIREMENTS.md) (RF-01…RF-04) · [PROJECT.md §4](../PROJECT.md) (arquitectura del grafo)
