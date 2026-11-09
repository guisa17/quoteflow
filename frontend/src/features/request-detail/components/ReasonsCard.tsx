import { REASON_LABELS } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import type { ApprovalReason } from '@/types/api'

/** Por qué la solicitud no siguió de largo: la regla de negocio que actuó.
 * Puede haber varios motivos de aprobación a la vez (BR-09). */
export function ReasonsCard({
  approvalReasons,
  rejectionReason,
  blockingReason,
}: {
  approvalReasons: ApprovalReason[]
  rejectionReason: ApprovalReason | null
  blockingReason: ApprovalReason | null
}) {
  const items: { reason: ApprovalReason; kind: 'block' | 'reject' | 'approve' }[] = [
    ...(blockingReason ? [{ reason: blockingReason, kind: 'block' as const }] : []),
    ...(rejectionReason ? [{ reason: rejectionReason, kind: 'reject' as const }] : []),
    ...approvalReasons.map((reason) => ({ reason, kind: 'approve' as const })),
  ]
  if (items.length === 0) return null

  const title =
    items[0].kind === 'approve'
      ? items.length > 1
        ? 'Por qué requiere aprobación'
        : 'Por qué requiere aprobación'
      : items[0].kind === 'reject'
        ? 'Por qué se rechazó'
        : 'Por qué se detuvo'

  return (
    <section aria-labelledby="reasons-title">
      <h2 id="reasons-title" className="field-label">
        {title}
      </h2>
      <ul className="mt-2 space-y-1.5">
        {items.map(({ reason, kind }, i) => (
          <li
            key={i}
            className={cn(
              'grid gap-x-4 gap-y-0.5 rounded-sm px-3 py-2 sm:grid-cols-[14rem_1fr]',
              kind === 'approve' && 'bg-canary text-canary-ink',
              kind === 'reject' && 'bg-red text-red-ink',
              kind === 'block' && 'bg-violet text-violet-ink',
            )}
          >
            <span className="text-sm font-bold">{REASON_LABELS[reason.reason_code]}</span>
            <span className="text-sm">{reason.detail}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
