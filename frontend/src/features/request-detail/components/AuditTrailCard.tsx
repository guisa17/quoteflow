import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate } from '@/lib/money'
import type { AuditEvent } from '@/types/api'

/** RF-09.3 — "trazabilidad": la secuencia de nodos del grafo que procesó la
 * solicitud (RF-08). Se muestra en orden de ejecución, no el más reciente
 * primero -- es una traza, se lee de arriba hacia abajo como ocurrió. */
export function AuditTrailCard({ events }: { events: AuditEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Trazabilidad</CardTitle>
        <CardDescription>Secuencia de nodos ejecutados, en orden (RF-08).</CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="space-y-0">
          {events.map((event, i) => (
            <li key={i} className="border-border relative flex gap-3 border-l pb-4 pl-4 last:border-transparent last:pb-0">
              <span
                aria-hidden
                className="bg-primary absolute top-1 -left-[3.5px] size-1.5 shrink-0 rounded-full"
              />
              <div className="min-w-0">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-figures text-xs font-semibold">{event.node}</span>
                  <span className="text-muted-foreground text-xs">{formatDate(event.timestamp)}</span>
                </div>
                <p className="text-muted-foreground mt-0.5 text-sm">{event.note}</p>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}
