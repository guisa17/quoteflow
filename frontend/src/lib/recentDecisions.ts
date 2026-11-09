import type { DecisionAction, Outcome } from '@/types/api'

/** Decisiones tomadas en esta pestaña, la más reciente primero. Sirven para
 * que la bandeja muestre qué folio acabas de decidir: al aprobar, el folio
 * cambia de grupo y sin esta marca es fácil perderlo de vista. */
export type RecentDecision = {
  requestId: string
  action: DecisionAction
  outcome: Outcome
  at: number
}

const STORAGE_KEY = 'quoteflow.recentDecisions'
const MAX = 10

export const ACTION_PAST: Record<DecisionAction, string> = {
  APPROVE: 'Aprobada',
  REJECT: 'Rechazada',
  OBSERVE: 'Observada',
}

export function readRecentDecisions(): RecentDecision[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? (parsed as RecentDecision[]) : []
  } catch {
    return []
  }
}

export function recordDecision(decision: Omit<RecentDecision, 'at'>) {
  const next = [
    { ...decision, at: Date.now() },
    ...readRecentDecisions().filter((d) => d.requestId !== decision.requestId),
  ].slice(0, MAX)
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    // Sin almacenamiento: la bandeja simplemente no marca la fila.
  }
}

export function clearRecentDecisions() {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // Nada que limpiar.
  }
}
