import { AlertOctagon, ShieldAlert, XCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { REASON_LABELS } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import type { ApprovalReason } from '@/types/api'

interface ReasonGroup {
  icon: LucideIcon
  tone: 'warning' | 'destructive'
  title: string
  reasons: ApprovalReason[]
}

/** RF-09.3 — "riesgos/motivos": por qué la solicitud no siguió de largo a
 * `DRAFT_READY`. BR-09 permite varios motivos de aprobación concurrentes,
 * así que esto siempre es una lista, nunca un único valor. */
export function ReasonsCard({
  approvalReasons,
  rejectionReason,
  blockingReason,
}: {
  approvalReasons: ApprovalReason[]
  rejectionReason: ApprovalReason | null
  blockingReason: ApprovalReason | null
}) {
  const groups: ReasonGroup[] = []
  if (blockingReason) {
    groups.push({ icon: AlertOctagon, tone: 'warning', title: 'Motivo de bloqueo', reasons: [blockingReason] })
  }
  if (rejectionReason) {
    groups.push({ icon: XCircle, tone: 'destructive', title: 'Motivo de rechazo', reasons: [rejectionReason] })
  }
  if (approvalReasons.length > 0) {
    groups.push({
      icon: ShieldAlert,
      tone: 'warning',
      title: `Motivo${approvalReasons.length > 1 ? 's' : ''} de aprobación (BR-09)`,
      reasons: approvalReasons,
    })
  }

  if (groups.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>Riesgos y motivos</CardTitle>
        <CardDescription>Reglas de negocio que determinaron el resultado.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {groups.map((group) => (
          <div key={group.title} className="space-y-2">
            <p
              className={cn(
                'flex items-center gap-1.5 text-xs font-semibold',
                group.tone === 'destructive' ? 'text-destructive' : 'text-warning',
              )}
            >
              <group.icon aria-hidden className="size-3.5" />
              {group.title}
            </p>
            <ul className="space-y-1.5">
              {group.reasons.map((reason, i) => (
                <li key={i} className="bg-muted/60 rounded-md px-3 py-2 text-sm">
                  <span className="font-figures block text-xs font-medium">
                    {REASON_LABELS[reason.reason_code]} ({reason.reason_code})
                  </span>
                  <span className="text-muted-foreground">{reason.detail}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
