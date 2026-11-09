import { OUTCOME_META, TINT_CLASSES } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import type { Outcome } from '@/types/api'

/** El resultado como copia del talonario: tinte de papel, tinta, ícono y texto. */
export function OutcomeBadge({
  outcome,
  size = 'sm',
  className,
}: {
  outcome: Outcome
  size?: 'sm' | 'lg'
  className?: string
}) {
  const meta = OUTCOME_META[outcome]
  const tint = TINT_CLASSES[meta.tint]
  const Icon = meta.icon
  return (
    <span
      className={cn(
        'inline-flex w-fit shrink-0 items-center gap-1.5 rounded-full font-semibold whitespace-nowrap',
        tint.surface,
        tint.ink,
        size === 'sm' ? 'py-0.5 pr-2 pl-1.5 text-xs' : 'py-1 pr-3 pl-2.5 text-sm',
        className,
      )}
    >
      <Icon aria-hidden className={cn('shrink-0 stroke-[2.25]', size === 'sm' ? 'size-3.5' : 'size-4')} />
      {meta.label}
    </span>
  )
}
