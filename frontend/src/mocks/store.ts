/**
 * "Base de datos" del modo mock: solicitudes en memoria, persistidas en
 * `localStorage` para que sobrevivan a un refresh (analogía deliberada de
 * RNF-02 — reanudación durable — aunque aquí sea solo por comodidad de
 * demo, no por un checkpointer real).
 *
 * Al primer arranque se siembra con los 8 escenarios de
 * `backend/app/data/sample_requests.json` ya corridos por `engine.ts`, así
 * `npm run dev` abre con una bandeja poblada con los cinco `outcome`
 * representados, sin que el usuario tenga que crear nada primero.
 */

import { runIntake, applyDecision, makeHumanDecision, type ResumeResult } from '@/mocks/engine'
import { SCENARIOS } from '@/mocks/data'
import type {
  DecisionAction,
  HumanDecision,
  ReasonCode,
  RequestDetail,
  RequestSummary,
} from '@/types/api'

const STORAGE_KEY = 'quoteflow.mock.v1'

interface PausedState {
  tier: 'GOLD' | 'SILVER' | 'STANDARD'
  customerIsKnown: boolean
  resolvedLines: { sku: string; product_name: string; quantity: number; unit_price: string }[]
  discountPct: string
}

interface StoredRequest {
  detail: RequestDetail
  paused: PausedState | null
  appliedDecisionIds: string[]
}

interface PersistedShape {
  requests: StoredRequest[]
}

let cache: Map<string, StoredRequest> | null = null

function load(): Map<string, StoredRequest> {
  if (cache) return cache
  cache = new Map()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as PersistedShape
      for (const entry of parsed.requests) {
        cache.set(entry.detail.id, entry)
      }
      return cache
    }
  } catch {
    // localStorage no disponible o corrupto: se reconstruye desde el seed.
  }
  seed(cache)
  persist(cache)
  return cache
}

function persist(map: Map<string, StoredRequest>) {
  try {
    const payload: PersistedShape = { requests: [...map.values()] }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // Cuota excedida o localStorage bloqueado: la sesión sigue funcionando
    // en memoria, solo no persiste entre recargas.
  }
}

let idCounter = 0
function nextId(): string {
  idCounter += 1
  const rand = Math.random().toString(36).slice(2, 6)
  return `req_${Date.now().toString(36)}${idCounter}${rand}`
}

function seed(map: Map<string, StoredRequest>) {
  // Escalonadas en el tiempo (la más antigua primero) para que la bandeja,
  // ordenada por actualización, cuente una historia creíble de una jornada
  // de trabajo en vez de 8 filas con el mismo timestamp.
  const baseMs = Date.now() - SCENARIOS.length * 45 * 60 * 1000
  SCENARIOS.forEach((scenario, index) => {
    const createdMs = baseMs + index * 45 * 60 * 1000
    const stored = buildFromIntake(scenario.customer_id, scenario.raw_text, createdMs)
    map.set(stored.detail.id, stored)
  })
}

function buildFromIntake(customerId: string, rawText: string, atMs: number): StoredRequest {
  const result = runIntake(customerId, rawText, atMs)
  const nowIso = new Date(atMs).toISOString()
  const detail: RequestDetail = {
    id: nextId(),
    thread_id: `thread_${Math.random().toString(36).slice(2, 10)}`,
    customer_id: customerId,
    customer_name: result.customer_name,
    raw_text: rawText,
    outcome: result.outcome,
    extraction: result.extraction,
    quote: result.quote,
    approval_reasons: result.approval_reasons,
    rejection_reason: result.rejection_reason,
    blocking_reason: result.blocking_reason,
    audit_trail: result.audit_trail,
    human_decision: null,
    draft_text: result.draft,
    created_at: nowIso,
    updated_at: nowIso,
  }
  return { detail, paused: result.paused, appliedDecisionIds: [] }
}

/** RF-08 (motivo principal): derivado de los campos ya presentes en el
 * detalle -- no se guarda por separado, así nunca puede desincronizarse. */
export function deriveReasonCode(detail: RequestDetail): ReasonCode | null {
  switch (detail.outcome) {
    case 'DRAFT_READY':
      return null
    case 'NEEDS_CLARIFICATION':
    case 'BLOCKED':
      return detail.blocking_reason?.reason_code ?? null
    case 'REJECTED_BY_POLICY':
      return detail.rejection_reason?.reason_code ?? detail.approval_reasons[0]?.reason_code ?? null
    case 'PENDING_APPROVAL':
      return detail.approval_reasons[0]?.reason_code ?? null
  }
}

function buildSummary(detail: RequestDetail): string {
  const items = detail.extraction?.items ?? []
  if (items.length > 0) {
    return items.map((i) => `${i.quantity ?? '?'} x ${i.product_reference}`).join(' + ')
  }
  const trimmed = detail.raw_text.trim()
  return trimmed.length > 60 ? `${trimmed.slice(0, 57)}...` : trimmed
}

function toSummary(detail: RequestDetail): RequestSummary {
  return {
    id: detail.id,
    customer_id: detail.customer_id,
    customer_name: detail.customer_name,
    summary: buildSummary(detail),
    outcome: detail.outcome,
    reason_code: deriveReasonCode(detail),
    updated_at: detail.updated_at,
  }
}

// ── Operaciones expuestas (misma forma que los 4 endpoints, RF-01..RF-04) ──

export function listRequests(): RequestSummary[] {
  const map = load()
  return [...map.values()]
    .map((s) => toSummary(s.detail))
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
}

export function getRequest(id: string): RequestDetail | null {
  const map = load()
  return map.get(id)?.detail ?? null
}

export function createRequest(customerId: string, rawText: string): RequestDetail {
  const map = load()
  const stored = buildFromIntake(customerId, rawText, Date.now())
  map.set(stored.detail.id, stored)
  persist(map)
  return stored.detail
}

export type DecisionResult =
  | { ok: true; detail: RequestDetail }
  | { ok: false; error: 'not_found' }
  | { ok: false; error: 'invalid_action' }
  | { ok: false; error: 'conflict' }

const VALID_ACTIONS: DecisionAction[] = ['APPROVE', 'REJECT', 'OBSERVE']

export function submitDecision(
  id: string,
  decisionId: string,
  action: DecisionAction,
  actor: string,
  comment: string | undefined,
): DecisionResult {
  const map = load()
  const stored = map.get(id)
  if (!stored) return { ok: false, error: 'not_found' }
  if (!VALID_ACTIONS.includes(action)) return { ok: false, error: 'invalid_action' }

  // BR-15: reenviar la misma decisión no tiene efecto. BR-19: una decisión que
  // contradice lo registrado se reporta. Puerto de `app/domain/decisions.py`.
  if (stored.appliedDecisionIds.includes(decisionId)) {
    const last = stored.detail.human_decision
    const priorAction = last?.decision_id === decisionId ? last.action : 'OBSERVE'
    return priorAction === action
      ? { ok: true, detail: stored.detail }
      : { ok: false, error: 'conflict' }
  }
  if (stored.paused === null) return { ok: false, error: 'conflict' }

  const nowMs = Date.now()
  const nowIso = new Date(nowMs).toISOString()
  const humanDecision: HumanDecision = makeHumanDecision(
    decisionId,
    action,
    actor,
    comment ?? null,
    nowIso,
  )

  const resume: ResumeResult = applyDecision(
    stored.detail,
    stored.paused,
    action,
    actor,
    comment ?? null,
    nowMs,
  )

  const nextDetail: RequestDetail = {
    ...stored.detail,
    outcome: resume.outcome,
    quote: resume.quote,
    draft_text: resume.draft,
    human_decision: humanDecision,
    audit_trail: [...stored.detail.audit_trail, ...resume.audit_events],
    updated_at: nowIso,
  }

  const nextStored: StoredRequest = {
    detail: nextDetail,
    // OBSERVE mantiene el caso en pausa (BR-14); APPROVE/REJECT lo resuelven.
    paused: action === 'OBSERVE' ? stored.paused : null,
    appliedDecisionIds: [...stored.appliedDecisionIds, decisionId],
  }
  map.set(id, nextStored)
  persist(map)
  return { ok: true, detail: nextDetail }
}

/** Usado por el botón "Reiniciar datos de demostración" de la bandeja
 * (no forma parte de RF-09; es una comodidad para volver a un estado
 * conocido sin recargar manualmente el localStorage del navegador). */
export function resetDemoData(): void {
  const map = new Map<string, StoredRequest>()
  seed(map)
  persist(map)
  cache = map
}
