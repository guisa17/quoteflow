import { cn } from '@/lib/utils'
import type { AuditEvent } from '@/types/api'

const TIME = new Intl.DateTimeFormat('es-PE', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
})

function time(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : TIME.format(d)
}

/** La traza completa en orden de ejecución, como el registro al reverso del
 * formulario: hora, etapa y lo que pasó. */
export function AuditTrailCard({ events }: { events: AuditEvent[] }) {
  return (
    <section aria-labelledby="audit-title">
      <h2 id="audit-title" className="field-label">
        Registro de auditoría · {events.length} eventos
      </h2>
      <div className="border-rule-strong mt-2 overflow-x-auto rounded-lg border">
        <table className="w-full min-w-[32rem] text-left text-[0.8125rem]">
          <tbody>
            {events.map((event, i) => {
              const alert = event.reason_code === 'SUSPECTED_MANIPULATION'
              return (
                <tr key={i} className={cn('border-rule border-b last:border-0', alert && 'bg-red/60')}>
                  <td className="font-figures text-ink-faint w-20 py-1.5 pl-3 align-top text-xs">
                    {time(event.timestamp)}
                  </td>
                  <td className="font-code w-40 py-1.5 pl-2 align-top text-xs">{event.node}</td>
                  <td className={cn('py-1.5 pr-3 pl-2 align-top', alert ? 'text-red-ink font-semibold' : 'text-ink-soft')}>
                    {event.note}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
