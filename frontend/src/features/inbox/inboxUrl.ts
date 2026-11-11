import type { Outcome } from '@/types/api'

/**
 * El estado de la bandeja vive en la URL (Atrás, recargar y compartir un
 * enlace conservan la vista). Reglas de la forma canónica:
 *
 * - Una sola convención: valores en minúsculas y en español, nunca los
 *   códigos internos de la API (`PENDING_APPROVAL`).
 * - Nada redundante: un `estado` ya implica la vista "Todas".
 * - Sin parámetros, la vista se elige sola (la cola si hay pendientes). Una
 *   pestaña elegida a mano sí se escribe, para que no dependa de los datos.
 * - "Pendiente de aprobación" es la vista "Por decidir", no un filtro de
 *   "Todas": así no hay dos caminos a la misma lista.
 * - Las URLs antiguas (`?vista=todas&estado=PENDING_APPROVAL`) se siguen
 *   entendiendo y se reescriben a la forma canónica.
 */

export type InboxView = 'pending' | 'all'

export interface InboxState {
  /** `null` si la URL no elige vista: se decide con `resolveView`. */
  view: InboxView | null
  /** Filtro de estado dentro de "Todas". Nunca `PENDING_APPROVAL`. */
  status: Outcome | null
}

const VIEW_SLUG: Record<InboxView, string> = { pending: 'por-decidir', all: 'todas' }

export const STATUS_SLUG: Record<Outcome, string> = {
  PENDING_APPROVAL: 'pendiente',
  NEEDS_CLARIFICATION: 'aclaracion',
  DRAFT_READY: 'borrador-listo',
  BLOCKED: 'detenida',
  REJECTED_BY_POLICY: 'rechazada',
}

const OUTCOMES = Object.keys(STATUS_SLUG) as Outcome[]

function parseStatus(value: string | null): Outcome | null {
  if (!value) return null
  return OUTCOMES.find((o) => STATUS_SLUG[o] === value || o === value) ?? null
}

/** Normaliza lo que diga la URL, incluidas las formas antiguas. */
export function normalizeState(state: InboxState): InboxState {
  if (state.status === 'PENDING_APPROVAL') return { view: 'pending', status: null }
  if (state.status) return { view: 'all', status: state.status }
  return state
}

export function parseInboxParams(params: URLSearchParams): InboxState {
  const vista = params.get('vista')
  const view = vista === VIEW_SLUG.all ? 'all' : vista === VIEW_SLUG.pending ? 'pending' : null
  return normalizeState({ view, status: parseStatus(params.get('estado')) })
}

/** Sin elección explícita, abre la cola si hay algo por decidir. */
export function resolveView(state: InboxState, pendingCount: number, loading: boolean): InboxView {
  if (state.view) return state.view
  return loading || pendingCount > 0 ? 'pending' : 'all'
}

/** Parámetros canónicos para un estado de la bandeja. */
export function inboxSearch(state: InboxState): Record<string, string> {
  const { view, status } = normalizeState(state)
  if (status) return { estado: STATUS_SLUG[status] }
  return view ? { vista: VIEW_SLUG[view] } : {}
}
