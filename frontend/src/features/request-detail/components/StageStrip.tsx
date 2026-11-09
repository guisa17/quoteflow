import { Check, Clock3, Minus, X } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { AuditEvent, Outcome } from '@/types/api'

/** Las doce etapas del grafo, siempre en la misma posición: dos solicitudes
 * se comparan de un vistazo porque cada etapa ocupa su casilla fija. */
const STAGES: { node: string; label: string }[] = [
  { node: 'ingest', label: 'Registro' },
  { node: 'extract', label: 'Lectura' },
  { node: 'resolve_customer', label: 'Cliente' },
  { node: 'validate_request', label: 'Datos' },
  { node: 'resolve_catalog', label: 'Catálogo' },
  { node: 'check_inventory', label: 'Stock' },
  { node: 'price_quote', label: 'Precio' },
  { node: 'evaluate_policy', label: 'Política' },
  { node: 'human_approval', label: 'Aprobación' },
  { node: 'apply_decision', label: 'Decisión' },
  { node: 'compose_draft', label: 'Borrador' },
  { node: 'finalize', label: 'Cierre' },
]

type StageState = 'done' | 'stopped' | 'waiting' | 'skipped'

const STOP_OUTCOMES: Outcome[] = ['NEEDS_CLARIFICATION', 'BLOCKED', 'REJECTED_BY_POLICY']

function stageStates(events: AuditEvent[], outcome: Outcome): StageState[] {
  const visited = new Set(events.map((e) => e.node))
  const order = events.map((e) => e.node).filter((n) => n !== 'finalize')
  const lastWork = order[order.length - 1]

  return STAGES.map(({ node }) => {
    if (outcome === 'PENDING_APPROVAL' && node === 'human_approval') return 'waiting'
    if (!visited.has(node)) return 'skipped'
    if (STOP_OUTCOMES.includes(outcome) && node === lastWork) return 'stopped'
    return 'done'
  })
}

const STATE_LABEL: Record<StageState, string> = {
  done: 'completada',
  stopped: 'aquí se detuvo',
  waiting: 'en espera',
  skipped: 'no recorrida',
}

export function StageStrip({ events, outcome }: { events: AuditEvent[]; outcome: Outcome }) {
  const states = stageStates(events, outcome)
  const notes = new Map<string, string>()
  for (const e of events) notes.set(e.node, e.note)

  return (
    <section aria-labelledby="stages-title">
      <h2 id="stages-title" className="field-label">
        Recorrido
      </h2>
      <ol className="mt-2 grid grid-cols-4 gap-0.5 sm:grid-cols-6 xl:grid-cols-12">
        {STAGES.map((stage, i) => {
          const state = states[i]
          const Icon = state === 'done' ? Check : state === 'stopped' ? X : state === 'waiting' ? Clock3 : Minus
          return (
            <li
              key={stage.node}
              title={notes.get(stage.node) ?? `${stage.label}: ${STATE_LABEL[state]}`}
              className={cn(
                'flex min-w-0 flex-col gap-1.5 rounded-md px-1.5 pt-2 pb-1.5',
                state === 'done' && 'bg-paper-ruled',
                state === 'stopped' && 'bg-red text-red-ink',
                state === 'waiting' && 'bg-canary text-canary-ink',
                state === 'skipped' && 'text-ink-faint bg-paper-ruled/40',
              )}
            >
              <span className="flex items-center justify-between">
                <span className="font-figures text-[0.6875rem] opacity-70">{String(i + 1).padStart(2, '0')}</span>
                <Icon aria-hidden className={cn('size-3.5 stroke-[2.5]', state === 'done' && 'text-ink')} />
              </span>
              <span
                className={cn(
                  'truncate text-xs leading-tight xl:text-[0.6875rem] xl:tracking-[-0.01em]',
                  state === 'skipped' ? 'font-normal' : 'font-semibold',
                )}
              >
                {stage.label}
                <span className="sr-only">, {STATE_LABEL[state]}</span>
              </span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
