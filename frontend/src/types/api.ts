/**
 * Tipos compartidos del contrato RF-01…RF-04.
 *
 * Copiados 1:1 de `docs/API_CONTRACT.md` — esa es la fuente de verdad fija;
 * este archivo no la reinterpreta. Si algún día discrepan, se corrige aquí,
 * no al revés (API_CONTRACT.md § "Regla de precedencia").
 *
 * Recordatorio del contrato: todo monto monetario viaja como `string`
 * decimal (nunca `number`) para no arriesgar precisión en el borde de red
 * (la misma razón de BR-04, aplicada al HTTP). Este frontend nunca hace
 * aritmética con esos strings — solo los formatea para mostrar
 * (ver `src/lib/money.ts`).
 */

export type Outcome =
  | 'NEEDS_CLARIFICATION'
  | 'DRAFT_READY'
  | 'BLOCKED'
  | 'PENDING_APPROVAL'
  | 'REJECTED_BY_POLICY'

export type ReasonCode =
  | 'MISSING_PRODUCT_REFERENCE'
  | 'MISSING_QUANTITY'
  | 'UNKNOWN_SKU'
  | 'INSUFFICIENT_STOCK'
  | 'THRESHOLD_EXCEEDED'
  | 'DISCOUNT_EXCEPTION'
  | 'UNKNOWN_CUSTOMER'
  | 'DISCOUNT_ABOVE_HARD_CEILING'
  | 'EXTRACTION_FAILED'

export type DecisionAction = 'APPROVE' | 'REJECT' | 'OBSERVE'

export interface ApprovalReason {
  reason_code: ReasonCode
  detail: string
}

export interface ExtractedLineItem {
  product_reference: string
  quantity: number | null
}

export interface Extraction {
  items: ExtractedLineItem[]
  site: string | null
  requested_date: string | null
  requested_discount_pct: string | null // string decimal o null
}

export interface QuoteLine {
  sku: string
  product_name: string
  quantity: number
  unit_price: string // string decimal
  line_subtotal: string // string decimal
}

export interface Quote {
  lines: QuoteLine[]
  subtotal: string
  discount_pct: string
  discount_amount: string
  net: string
  tax_amount: string
  total: string
  currency: string
}

export interface AuditEvent {
  node: string // nombre del nodo del grafo que lo generó
  timestamp: string
  note: string
}

export interface HumanDecision {
  decision_id: string
  action: DecisionAction
  actor: string
  comment: string | null
  timestamp: string
}

// ── RF-01 · POST /requests ──────────────────────────────────────────

export interface CreateRequestBody {
  customer_id: string
  raw_text: string
}

// ── RF-02 · GET /requests ───────────────────────────────────────────

export interface RequestSummary {
  id: string
  customer_id: string
  customer_name: string // "" si el cliente es desconocido (BR-08)
  summary: string // ej. "20 x HX-200"
  outcome: Outcome
  reason_code: ReasonCode | null // el motivo principal si no es DRAFT_READY
  updated_at: string
}

export type RequestListResponse = RequestSummary[]

// ── RF-03 · GET /requests/{id} ──────────────────────────────────────

export interface RequestDetail {
  id: string
  thread_id: string
  customer_id: string
  customer_name: string
  raw_text: string
  outcome: Outcome

  extraction: Extraction | null // null si falló la extracción (EXTRACTION_FAILED)
  quote: Quote | null // null si el outcome no llegó a calcular (NEEDS_CLARIFICATION, BLOCKED)
  approval_reasons: ApprovalReason[] // BR-09: puede haber varios, concurrentes
  rejection_reason: ApprovalReason | null // BR-07: presente solo si outcome = REJECTED_BY_POLICY
  blocking_reason: ApprovalReason | null // presente solo si outcome = BLOCKED o NEEDS_CLARIFICATION

  audit_trail: AuditEvent[]
  human_decision: HumanDecision | null // null hasta que alguien decide
  draft_text: string | null // solo si outcome = DRAFT_READY

  created_at: string
  updated_at: string
}

// ── RF-04 · POST /requests/{id}/decision ────────────────────────────

export interface DecisionBody {
  decision_id: string // el frontend genera un UUID al montar el panel de decisión
  action: DecisionAction
  actor: string
  comment?: string
}

// ── Errores ──────────────────────────────────────────────────────────

export interface ApiError {
  detail: string
}
