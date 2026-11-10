import { Stamp } from '@/features/request-detail/components/Stamp'
import { formatDate } from '@/lib/money'
import { NEXT_STEP, OUTCOME_META, TINT_CLASSES } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import type { HumanDecision, Outcome } from '@/types/api'

/** Columna derecha cuando no hay decisión pendiente: el resultado, el
 * siguiente paso y, si alguien decidió, su sello. */
export function OutcomePanel({
  outcome,
  decision,
  freshStamp,
}: {
  outcome: Outcome
  decision: HumanDecision | null
  freshStamp: boolean
}) {
  const meta = OUTCOME_META[outcome]
  const tint = TINT_CLASSES[meta.tint]
  const Icon = meta.icon
  return (
    <section aria-labelledby="outcome-title" className={cn('rounded-lg p-4', tint.surface, tint.ink)}>
      <h2 id="outcome-title" className="flex items-center gap-2 text-lg font-bold tracking-[-0.01em]">
        <Icon aria-hidden className="size-5 stroke-[2.25]" />
        {meta.label}
      </h2>
      <p className="mt-1.5 text-sm">{meta.description}</p>
      <p className="mt-3 text-sm font-semibold">{NEXT_STEP[outcome]}</p>
      {decision && (
        <div className="mt-4 border-t border-current/20 pt-3">
          {/* En pantallas angostas el sello vive aquí; desde sm cae sobre el total. */}
          <Stamp decision={decision} fresh={freshStamp} className="mb-3 sm:hidden" />
          <p className="text-sm">
            <span className="font-semibold">
              {{ APPROVE: 'Aprobada', REJECT: 'Rechazada', OBSERVE: 'Observada' }[decision.action]}
            </span>{' '}
            por {decision.actor}
            <span className="font-figures block text-xs opacity-80">{formatDate(decision.timestamp)}</span>
          </p>
          {decision.comment && <p className="mt-2 text-sm">“{decision.comment}”</p>}
        </div>
      )}
      {!decision && (
        <p className="mt-3 text-xs opacity-80">Resuelto por las reglas, sin intervención humana.</p>
      )}
    </section>
  )
}
