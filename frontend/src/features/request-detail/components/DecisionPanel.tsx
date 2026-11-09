import { Check, Eye, Loader2, X } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useSubmitDecision } from '@/hooks/useRequests'
import { formatDate } from '@/lib/money'
import { OUTCOME_META } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import type { ApprovalReason, DecisionAction, HumanDecision } from '@/types/api'

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

const ACTION_WORD: Record<DecisionAction, string> = {
  APPROVE: 'Aprobado',
  REJECT: 'Rechazado',
  OBSERVE: 'Observado',
}

/** La única placa invertida de la pantalla: la decisión pendiente. El
 * `decision_id` se conserva solo al reintentar la misma acción tras un fallo
 * (BR-15); cambiar de acción o tener éxito usa uno nuevo, porque repetir un id
 * con otra acción es un conflicto (BR-19). */
export function DecisionPanel({
  requestId,
  lastDecision,
  approvalReasons,
  onDecided,
}: {
  requestId: string
  lastDecision: HumanDecision | null
  approvalReasons: ApprovalReason[]
  onDecided: () => void
}) {
  const [failedAttempt, setFailedAttempt] = useState<{ id: string; action: DecisionAction } | null>(null)
  const [actor, setActor] = useState(readStoredActor)
  const [comment, setComment] = useState('')
  const [pendingAction, setPendingAction] = useState<DecisionAction | null>(null)
  const [actorMissing, setActorMissing] = useState(false)
  const submitDecision = useSubmitDecision(requestId)

  async function handleDecide(action: DecisionAction) {
    if (actor.trim().length === 0) {
      setActorMissing(true)
      document.getElementById('decision-actor')?.focus()
      return
    }
    setPendingAction(action)
    const decisionId = failedAttempt?.action === action ? failedAttempt.id : newDecisionId()
    try {
      try {
        localStorage.setItem(ACTOR_STORAGE_KEY, actor.trim())
      } catch {
        // Sin almacenamiento: no bloquea el envío.
      }
      const detail = await submitDecision.mutateAsync({
        decision_id: decisionId,
        action,
        actor: actor.trim(),
        comment: comment.trim() || undefined,
      })
      setFailedAttempt(null)
      setComment('')
      onDecided()
      toast.success(`${ACTION_WORD[action]}. ${OUTCOME_META[detail.outcome].label}.`)
    } catch (err) {
      setFailedAttempt({ id: decisionId, action })
      toast.error('No se registró la decisión', {
        description: err instanceof Error ? err.message : 'Error desconocido.',
      })
    } finally {
      setPendingAction(null)
    }
  }

  const busy = submitDecision.isPending

  return (
    <section aria-labelledby="decision-title" className="bg-plate text-plate-ink rounded-md p-4">
      <h2 id="decision-title" className="text-lg font-bold tracking-[-0.01em]">
        Tu decisión
      </h2>
      <p className="text-plate-ink-soft mt-1 text-sm">
        {approvalReasons.length > 1
          ? `${approvalReasons.length} motivos requieren aprobación; una sola decisión los resuelve.`
          : 'Esta solicitud se detuvo para que alguien la apruebe.'}
      </p>

      {lastDecision && (
        <div className="border-plate-rule mt-3 border-t pt-3 text-xs">
          <span className="font-semibold">Observada</span> por {lastDecision.actor} ·{' '}
          <span className="font-figures">{formatDate(lastDecision.timestamp)}</span>
          {lastDecision.comment && <p className="text-plate-ink-soft mt-1">“{lastDecision.comment}”</p>}
        </div>
      )}

      <div className="mt-4 space-y-3">
        <label className="block">
          <span className="field-label !text-plate-ink-soft">Quién decide</span>
          <input
            id="decision-actor"
            value={actor}
            onChange={(e) => {
              setActor(e.target.value)
              setActorMissing(false)
            }}
            maxLength={254}
            aria-invalid={actorMissing}
            aria-describedby={actorMissing ? 'actor-error' : undefined}
            placeholder="jefe.comercial@ferrocima.example"
            className={cn(
              'bg-plate-field text-plate-ink placeholder:text-plate-ink-soft/70 mt-1 h-9 w-full rounded-sm border px-2.5 text-sm outline-none',
              actorMissing ? 'border-stamp-red' : 'border-plate-rule focus-visible:border-plate-ink',
            )}
          />
          {actorMissing && (
            <span id="actor-error" className="mt-1 block text-xs font-semibold">
              Escribe tu nombre o correo: queda en el sello y en la auditoría.
            </span>
          )}
        </label>
        <label className="block">
          <span className="field-label !text-plate-ink-soft">Comentario · opcional</span>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={2000}
            rows={3}
            placeholder="Condiciones o motivo, para la auditoría."
            className="bg-plate-field text-plate-ink placeholder:text-plate-ink-soft/70 border-plate-rule focus-visible:border-plate-ink mt-1 w-full resize-y rounded-sm border px-2.5 py-2 text-sm outline-none"
          />
        </label>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => handleDecide('APPROVE')}
          disabled={busy}
          className="bg-plate-ink text-plate col-span-2 inline-flex h-10 items-center justify-center gap-2 rounded-sm text-sm font-bold transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {pendingAction === 'APPROVE' ? <Loader2 aria-hidden className="size-4 animate-spin" /> : <Check aria-hidden className="size-4 stroke-[2.5]" />}
          Aprobar y generar borrador
        </button>
        <button
          type="button"
          onClick={() => handleDecide('REJECT')}
          disabled={busy}
          className="border-plate-rule hover:bg-plate-field inline-flex h-9 items-center justify-center gap-1.5 rounded-sm border text-sm font-semibold transition-colors disabled:opacity-50"
        >
          {pendingAction === 'REJECT' ? <Loader2 aria-hidden className="size-4 animate-spin" /> : <X aria-hidden className="size-4" />}
          Rechazar
        </button>
        <button
          type="button"
          onClick={() => handleDecide('OBSERVE')}
          disabled={busy}
          className="border-plate-rule hover:bg-plate-field inline-flex h-9 items-center justify-center gap-1.5 rounded-sm border text-sm font-semibold transition-colors disabled:opacity-50"
        >
          {pendingAction === 'OBSERVE' ? <Loader2 aria-hidden className="size-4 animate-spin" /> : <Eye aria-hidden className="size-4" />}
          Observar
        </button>
      </div>
      <p className="text-plate-ink-soft mt-3 text-xs">
        Observar deja constancia y mantiene el caso en pausa. Rechazar lo cierra.
      </p>
    </section>
  )
}
