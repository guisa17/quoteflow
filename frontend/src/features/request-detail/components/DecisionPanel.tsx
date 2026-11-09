import { Check, Eye, Loader2, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useSubmitDecision } from '@/hooks/useRequests'
import { formatDate } from '@/lib/money'
import type { DecisionAction, HumanDecision } from '@/types/api'

const ACTOR_STORAGE_KEY = 'quoteflow.actor'

function readStoredActor(): string {
  try {
    return localStorage.getItem(ACTOR_STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

function newDecisionId(): string {
  return typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `dec_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
}

/** RF-09.4 — panel de decisión: aprobar / rechazar / observar, con
 * comentario (BR-14). El `decision_id` se conserva solo al reintentar la misma
 * acción tras un fallo (BR-15); cambiar de acción o tener éxito usa uno nuevo,
 * porque repetir un id con otra acción es un conflicto (BR-19). */
export function DecisionPanel({
  requestId,
  lastDecision,
}: {
  requestId: string
  lastDecision: HumanDecision | null
}) {
  const [failedAttempt, setFailedAttempt] = useState<{ id: string; action: DecisionAction } | null>(null)
  const [actor, setActor] = useState(readStoredActor)
  const [comment, setComment] = useState('')
  const [pendingAction, setPendingAction] = useState<DecisionAction | null>(null)
  const submitDecision = useSubmitDecision(requestId)

  const actorValid = actor.trim().length > 0

  async function handleDecide(action: DecisionAction) {
    if (!actorValid) {
      toast.error('Indica quién decide antes de continuar.')
      return
    }
    setPendingAction(action)
    const decisionId = failedAttempt?.action === action ? failedAttempt.id : newDecisionId()
    try {
      try {
        localStorage.setItem(ACTOR_STORAGE_KEY, actor.trim())
      } catch {
        // localStorage no disponible: no bloquea el envío.
      }
      const detail = await submitDecision.mutateAsync({
        decision_id: decisionId,
        action,
        actor: actor.trim(),
        comment: comment.trim() || undefined,
      })
      setFailedAttempt(null)
      setComment('')
      const label = { APPROVE: 'Aprobada', REJECT: 'Rechazada', OBSERVE: 'Observación registrada' }[action]
      toast.success(label, { description: `Resultado actual: ${detail.outcome}` })
    } catch (err) {
      setFailedAttempt({ id: decisionId, action })
      toast.error('No se pudo registrar la decisión', {
        description: err instanceof Error ? err.message : 'Error desconocido.',
      })
    } finally {
      setPendingAction(null)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Decisión</CardTitle>
        <CardDescription>
          Aprobar avanza a borrador; rechazar cierra el caso; observar deja constancia sin
          resolver (BR-14) — el caso sigue en pausa.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {lastDecision && (
          <div className="bg-muted/60 rounded-md px-3 py-2 text-xs">
            <span className="font-medium">Última decisión registrada:</span>{' '}
            {lastDecision.action} por {lastDecision.actor} — {formatDate(lastDecision.timestamp)}
            {lastDecision.comment && (
              <p className="text-muted-foreground mt-1">"{lastDecision.comment}"</p>
            )}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="decision-actor">Actor (quién decide)</Label>
          <Input
            id="decision-actor"
            value={actor}
            onChange={(e) => setActor(e.target.value)}
            maxLength={254}
            placeholder="ej. jefe.comercial@ferrocima.example"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="decision-comment">Comentario (opcional)</Label>
          <Textarea
            id="decision-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={2000}
            placeholder="Motivo de la decisión, condiciones, o lo que deba quedar en la auditoría."
            rows={3}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => handleDecide('APPROVE')} disabled={submitDecision.isPending}>
            {pendingAction === 'APPROVE' ? <Loader2 aria-hidden className="animate-spin" /> : <Check aria-hidden />}
            Aprobar
          </Button>
          <Button
            variant="destructive"
            onClick={() => handleDecide('REJECT')}
            disabled={submitDecision.isPending}
          >
            {pendingAction === 'REJECT' ? <Loader2 aria-hidden className="animate-spin" /> : <X aria-hidden />}
            Rechazar
          </Button>
          <Button
            variant="outline"
            onClick={() => handleDecide('OBSERVE')}
            disabled={submitDecision.isPending}
          >
            {pendingAction === 'OBSERVE' ? <Loader2 aria-hidden className="animate-spin" /> : <Eye aria-hidden />}
            Observar
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
