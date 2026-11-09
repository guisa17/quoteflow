/**
 * Motor determinista del modo mock — puerto en TypeScript de
 * `backend/app/graph/nodes.py` + `app/domain/{validation,pricing,policy}.py`.
 *
 * No es una simulación superficial: implementa las mismas reglas de negocio
 * (BR-02, BR-04..BR-13) en el mismo orden que el grafo real, para que los 8
 * escenarios de `sample_requests.json` produzcan el mismo `outcome` aquí que
 * en el backend, y para que una solicitud nueva escrita en el formulario se
 * resuelva con reglas reales, no con datos inventados.
 *
 * Vive enteramente en `src/mocks/` — nada fuera de esta carpeta debe
 * importar reglas de negocio de aquí (CLAUDE.md §2, aplicado también a este
 * puerto de demostración).
 */

import { fromCents, pctOfCents, roundHalfUpCents, sumCents, toCents } from '@/mocks/decimal'
import { CUSTOMERS, INVENTORY, POLICY, PRODUCTS, type MockCustomer, type Tier } from '@/mocks/data'
import { fakeExtract } from '@/mocks/extract'
import type {
  ApprovalReason,
  AuditEvent,
  DecisionAction,
  Extraction,
  HumanDecision,
  Outcome,
  Quote,
  QuoteLine,
  ReasonCode,
  RequestDetail,
} from '@/types/api'

// ── Repositorios en memoria (equivalentes a app/domain/repositories.py) ──

function normalizeReference(reference: string): string {
  return reference.trim().toUpperCase().replace(/\s+/g, '').replace(/-+/g, '-')
}

function lookupCustomer(customerId: string): MockCustomer | null {
  const customer = CUSTOMERS.find((c) => c.customer_id === customerId)
  return customer && customer.active ? customer : null
}

function lookupProduct(reference: string) {
  const normalized = normalizeReference(reference)
  const product = PRODUCTS.find((p) => normalizeReference(p.sku) === normalized)
  return product && product.active ? product : null
}

function availableStock(sku: string): number | null {
  const records = INVENTORY.filter((r) => r.sku === sku)
  if (records.length === 0) return null
  // Disponible = on_hand - reserved, sumado entre almacenes (BR-13). No es
  // un monto monetario: se suma directo, sin pasar por `mocks/decimal.ts`.
  return records.reduce((acc, r) => acc + (r.on_hand - r.reserved), 0)
}

// ── Resultado interno del pipeline ────────────────────────────────────

interface ResolvedLine {
  sku: string
  product_name: string
  quantity: number
  unit_price: string
}

interface PipelineResult {
  customer_name: string
  extraction: Extraction | null
  quote: Quote | null
  approval_reasons: ApprovalReason[]
  rejection_reason: ApprovalReason | null
  blocking_reason: ApprovalReason | null
  outcome: Outcome
  reason_code: ReasonCode | null
  audit_trail: AuditEvent[]
  /** Solo si `outcome = DRAFT_READY` de una vez (sin pasar por aprobación). */
  draft: string | null
  /** Estado intermedio que necesita `applyDecision` para reanudar. */
  paused: {
    tier: Tier
    customerIsKnown: boolean
    resolvedLines: ResolvedLine[]
    discountPct: string
  } | null
}

function reason(code: ReasonCode, detail: string): ApprovalReason {
  return { reason_code: code, detail }
}

let auditClock = 0

function event(node: string, note: string, baseMs: number): AuditEvent {
  auditClock += 350 + Math.round(Math.random() * 250)
  return { node, note, timestamp: new Date(baseMs + auditClock).toISOString() }
}

/** RF-06/BR-04: subtotal -> descuento -> neto -> IGV -> total, en centavos
 * enteros con ROUND_HALF_UP explícito (puerto de `pricing.py`). */
function calculateQuote(lines: ResolvedLine[], discountPct: string): Quote {
  const quoteLines: QuoteLine[] = lines.map((line) => {
    const lineSubtotalCents = toCents(line.unit_price) * line.quantity
    return {
      sku: line.sku,
      product_name: line.product_name,
      quantity: line.quantity,
      unit_price: line.unit_price,
      line_subtotal: fromCents(lineSubtotalCents),
    }
  })

  const subtotalCents = sumCents(quoteLines.map((l) => toCents(l.line_subtotal)))
  const discountAmountCents = pctOfCents(subtotalCents, discountPct)
  const netCents = subtotalCents - discountAmountCents
  const taxRate = Number(POLICY.tax.rate)
  const taxAmountCents = roundHalfUpCents(netCents * taxRate)
  const totalCents = netCents + taxAmountCents

  return {
    lines: quoteLines,
    subtotal: fromCents(subtotalCents),
    discount_pct: discountPct,
    discount_amount: fromCents(discountAmountCents),
    net: fromCents(netCents),
    tax_amount: fromCents(taxAmountCents),
    total: fromCents(totalCents),
    currency: POLICY.currency,
  }
}

/** BR-05..BR-09: puerto de `policy.py`, mismo orden de evaluación. */
function evaluatePolicy(
  tier: Tier,
  customerIsKnown: boolean,
  requestedDiscountPct: string,
  netDecimal: string,
): { rejection: ApprovalReason | null; approvalReasons: ApprovalReason[] } {
  const requested = Number(requestedDiscountPct)
  const hardCeiling = Number(POLICY.hard_discount_ceiling_pct)

  if (requested > hardCeiling) {
    return {
      rejection: reason(
        'DISCOUNT_ABOVE_HARD_CEILING',
        `Descuento solicitado ${requestedDiscountPct}% supera el techo duro de ${POLICY.hard_discount_ceiling_pct}%.`,
      ),
      approvalReasons: [],
    }
  }

  const reasons: ApprovalReason[] = []

  if (!customerIsKnown) {
    reasons.push(
      reason('UNKNOWN_CUSTOMER', 'Cliente no registrado; se asigno nivel STANDARD provisional.'),
    )
  }

  const maxDiscount = Number(POLICY.discount_by_tier[tier].max_discount_pct)
  if (requested > maxDiscount) {
    reasons.push(
      reason(
        'DISCOUNT_EXCEPTION',
        `Descuento solicitado ${requestedDiscountPct}% supera el maximo de ${tier} (${POLICY.discount_by_tier[tier].max_discount_pct}%).`,
      ),
    )
  }

  const netCents = toCents(netDecimal)
  const thresholdCents = toCents(POLICY.approval_threshold_usd)
  if (netCents > thresholdCents) {
    reasons.push(
      reason(
        'THRESHOLD_EXCEEDED',
        `Neto ${netDecimal} supera el umbral de aprobacion de ${POLICY.approval_threshold_usd}.`,
      ),
    )
  }

  return { rejection: null, approvalReasons: reasons }
}

function composeDraft(customerId: string, quote: Quote): string {
  const linesText = quote.lines
    .map((l) => `  - ${l.quantity} x ${l.product_name} (${l.sku}) @ ${l.unit_price} c/u`)
    .join('\n')
  return (
    `Cotizacion para ${customerId}\n${linesText}\n` +
    `Subtotal: ${quote.subtotal} ${quote.currency}\n` +
    `Descuento (${quote.discount_pct}%): -${quote.discount_amount} ${quote.currency}\n` +
    `Neto: ${quote.net} ${quote.currency}\n` +
    `IGV: ${quote.tax_amount} ${quote.currency}\n` +
    `Total: ${quote.total} ${quote.currency}`
  )
}

/**
 * Corre el pipeline completo (`ingest -> ... -> evaluate_policy`) y se
 * detiene en cuanto hay un resultado terminal, o en `PENDING_APPROVAL`
 * esperando una decisión humana — igual que el `interrupt()` real, pero sin
 * checkpointer: `applyDecision` retoma desde `paused`.
 */
export function runIntake(customerId: string, rawText: string, nowMs: number): PipelineResult {
  const trail: AuditEvent[] = []
  trail.push(event('ingest', `Solicitud registrada para ${customerId}.`, nowMs))

  const extraction = fakeExtract(rawText.trim())
  trail.push(event('extract', `${extraction.items.length} item(s) extraido(s) del texto.`, nowMs))

  const customer = lookupCustomer(customerId)
  const customerIsKnown = customer !== null
  const tier: Tier = customer?.tier ?? 'STANDARD'
  trail.push(
    event(
      'resolve_customer',
      customerIsKnown
        ? `Cliente ${customerId} resuelto: nivel ${tier}.`
        : `Cliente ${customerId} no registrado; nivel STANDARD provisional (BR-08).`,
      nowMs,
    ),
  )

  const terminal = (
    outcome: Outcome,
    reasonCode: ReasonCode | null,
    opts: Partial<PipelineResult> = {},
  ): PipelineResult => {
    trail.push(
      event('finalize', `Resultado final: ${outcome}${reasonCode ? ` / ${reasonCode}` : ''}.`, nowMs),
    )
    return {
      customer_name: customer?.legal_name ?? '',
      extraction,
      quote: null,
      approval_reasons: [],
      rejection_reason: null,
      blocking_reason: null,
      outcome,
      reason_code: reasonCode,
      audit_trail: trail,
      draft: null,
      paused: null,
      ...opts,
    }
  }

  // BR-10/BR-11: completitud sobre la extraccion cruda.
  if (extraction.items.length === 0) {
    const r = reason('MISSING_PRODUCT_REFERENCE', 'No se identifico ningun producto en la solicitud.')
    trail.push(event('validate_request', r.detail, nowMs))
    return terminal('NEEDS_CLARIFICATION', r.reason_code, { blocking_reason: r })
  }
  for (const item of extraction.items) {
    if (item.quantity === null || item.quantity <= 0) {
      const r = reason(
        'MISSING_QUANTITY',
        `Falta una cantidad valida para '${item.product_reference}'.`,
      )
      trail.push(event('validate_request', r.detail, nowMs))
      return terminal('NEEDS_CLARIFICATION', r.reason_code, { blocking_reason: r })
    }
  }
  trail.push(event('validate_request', 'Solicitud completa (BR-10/11).', nowMs))

  // BR-02/BR-12: coincidencia exacta contra el catalogo, sin sustitucion.
  for (const item of extraction.items) {
    if (lookupProduct(item.product_reference) === null) {
      const r = reason(
        'UNKNOWN_SKU',
        `'${item.product_reference}' no existe en el catalogo o esta inactivo.`,
      )
      trail.push(event('resolve_catalog', r.detail, nowMs))
      return terminal('BLOCKED', r.reason_code, { blocking_reason: r })
    }
  }
  trail.push(
    event('resolve_catalog', `${extraction.items.length} item(s) resuelto(s) contra el catalogo (BR-02).`, nowMs),
  )

  // BR-13: disponible = on_hand - reserved, comparado con la cantidad acumulada por SKU.
  const resolvedLines: ResolvedLine[] = []
  const requested = new Map<string, number>()
  for (const item of extraction.items) {
    const product = lookupProduct(item.product_reference)
    if (product === null) continue // ya descartado arriba, defensivo
    const quantity = item.quantity ?? 0
    const requestedTotal = (requested.get(product.sku) ?? 0) + quantity
    requested.set(product.sku, requestedTotal)
    const available = availableStock(product.sku)
    if (available === null || requestedTotal > available) {
      const r = reason(
        'INSUFFICIENT_STOCK',
        `Disponible de ${product.sku}: ${available ?? 0}. Solicitado: ${requestedTotal}.`,
      )
      trail.push(event('check_inventory', r.detail, nowMs))
      return terminal('BLOCKED', r.reason_code, { blocking_reason: r })
    }
    resolvedLines.push({
      sku: product.sku,
      product_name: product.name,
      quantity,
      unit_price: product.list_price_usd,
    })
  }
  trail.push(event('check_inventory', `Stock suficiente para ${resolvedLines.length} linea(s) (BR-13).`, nowMs))

  // RF-06/BR-04: BR-11 -- descuento ausente se trata como 0%.
  const discountPct = extraction.requested_discount_pct ?? '0'
  const quote = calculateQuote(resolvedLines, discountPct)
  trail.push(
    event('price_quote', `Cotizado: subtotal ${quote.subtotal} neto ${quote.net} total ${quote.total}.`, nowMs),
  )

  // BR-05..BR-09
  const policyResult = evaluatePolicy(tier, customerIsKnown, discountPct, quote.net)
  if (policyResult.rejection !== null) {
    trail.push(event('evaluate_policy', policyResult.rejection.detail, nowMs))
    return terminal('REJECTED_BY_POLICY', policyResult.rejection.reason_code, {
      quote,
      rejection_reason: policyResult.rejection,
    })
  }

  if (policyResult.approvalReasons.length > 0) {
    trail.push(
      event('evaluate_policy', `${policyResult.approvalReasons.length} motivo(s) de aprobacion (BR-09).`, nowMs),
    )
    trail.push(event('human_approval', 'Solicitud en pausa, esperando decision humana (RF-07).', nowMs))
    return {
      customer_name: customer?.legal_name ?? '',
      extraction,
      quote,
      approval_reasons: policyResult.approvalReasons,
      rejection_reason: null,
      blocking_reason: null,
      outcome: 'PENDING_APPROVAL',
      reason_code: policyResult.approvalReasons[0].reason_code,
      audit_trail: trail,
      draft: null,
      paused: { tier, customerIsKnown, resolvedLines, discountPct },
    }
  }

  trail.push(event('evaluate_policy', 'Dentro de politica, sin aprobacion requerida.', nowMs))
  trail.push(event('compose_draft', 'Borrador generado por plantilla determinista.', nowMs))
  const draft = composeDraft(customerId, quote)
  return terminal('DRAFT_READY', null, { quote, draft })
}

// ── Reanudacion tras decision humana (BR-14..BR-16, RF-07) ─────────────

export interface ResumeResult {
  outcome: Outcome
  quote: Quote | null
  draft: string | null
  audit_events: AuditEvent[]
}

export function applyDecision(
  detail: RequestDetail,
  paused: PipelineResult['paused'],
  action: DecisionAction,
  actor: string,
  comment: string | null,
  nowMs: number,
): ResumeResult {
  const trail: AuditEvent[] = []
  trail.push(
    event(
      'apply_decision',
      `Decision ${action} aplicada por ${actor}${comment ? `: "${comment}"` : ''}.`,
      nowMs,
    ),
  )

  if (action === 'OBSERVE') {
    trail.push(event('human_approval', 'Observacion registrada; la solicitud sigue en pausa (BR-14).', nowMs))
    return {
      outcome: 'PENDING_APPROVAL',
      quote: detail.quote,
      draft: null,
      audit_events: trail,
    }
  }

  if (action === 'REJECT') {
    const reasonCode = detail.approval_reasons[0]?.reason_code ?? null
    trail.push(event('finalize', `Resultado final: REJECTED_BY_POLICY${reasonCode ? ` / ${reasonCode}` : ''}.`, nowMs))
    return {
      outcome: 'REJECTED_BY_POLICY',
      quote: detail.quote,
      draft: null,
      audit_events: trail,
    }
  }

  // APPROVE
  if (!paused || detail.quote === null) {
    throw new Error('applyDecision(APPROVE) requiere una cotizacion y estado en pausa.')
  }
  trail.push(event('compose_draft', 'Borrador generado por plantilla determinista.', nowMs))
  const draft = composeDraft(detail.customer_id, detail.quote)
  trail.push(event('finalize', 'Resultado final: DRAFT_READY.', nowMs))
  return {
    outcome: 'DRAFT_READY',
    quote: detail.quote,
    draft,
    audit_events: trail,
  }
}

export function makeHumanDecision(
  decisionId: string,
  action: DecisionAction,
  actor: string,
  comment: string | null,
  nowIso: string,
): HumanDecision {
  return { decision_id: decisionId, action, actor, comment, timestamp: nowIso }
}
