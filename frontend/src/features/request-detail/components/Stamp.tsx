import { formatDate } from '@/lib/money'
import { cn } from '@/lib/utils'
import type { HumanDecision } from '@/types/api'

const STAMP: Record<HumanDecision['action'], { word: string; className: string; rotate: string }> = {
  APPROVE: { word: 'Aprobado', className: 'text-stamp-blue', rotate: '-7deg' },
  REJECT: { word: 'Rechazado', className: 'text-stamp-red', rotate: '5deg' },
  OBSERVE: { word: 'Observado', className: 'text-stamp-ochre', rotate: '-3deg' },
}

/** La decisión humana como sello de goma: palabra, fecha y quien decidió.
 * `fresh` reproduce la caída del sello justo después de decidir. */
export function Stamp({ decision, fresh = false, className }: { decision: HumanDecision; fresh?: boolean; className?: string }) {
  const s = STAMP[decision.action]
  return (
    <div
      role="img"
      aria-label={`Sello: ${s.word} por ${decision.actor}, ${formatDate(decision.timestamp)}`}
      style={{ ['--stamp-rotate' as string]: s.rotate, transform: `rotate(${s.rotate})` }}
      className={cn(
        'pointer-events-none inline-flex flex-col items-center rounded-[6px] border-[3px] border-current px-3.5 pt-1.5 pb-1 mix-blend-multiply select-none dark:mix-blend-screen',
        'outline-2 outline-offset-[3px] outline-current',
        s.className,
        fresh && 'stamp-fresh',
        className,
      )}
    >
      <span className="condensed text-[1.375rem] leading-none font-extrabold tracking-[0.12em] uppercase">
        {s.word}
      </span>
      <span className="font-figures mt-1 text-[0.625rem] font-semibold tracking-wide uppercase">
        {formatDate(decision.timestamp)}
      </span>
      <span className="max-w-44 truncate text-[0.625rem] font-semibold">{decision.actor}</span>
    </div>
  )
}
