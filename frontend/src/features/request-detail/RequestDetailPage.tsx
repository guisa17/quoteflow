import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { OutcomeBadge } from '@/components/OutcomeBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { AuditTrailCard } from '@/features/request-detail/components/AuditTrailCard'
import { DecisionPanel } from '@/features/request-detail/components/DecisionPanel'
import { DraftCard } from '@/features/request-detail/components/DraftCard'
import { ExtractionCard } from '@/features/request-detail/components/ExtractionCard'
import { OutcomePanel } from '@/features/request-detail/components/OutcomePanel'
import { QuoteCard } from '@/features/request-detail/components/QuoteCard'
import { ReasonsCard } from '@/features/request-detail/components/ReasonsCard'
import { StageStrip } from '@/features/request-detail/components/StageStrip'
import { useRequestDetail, useRequestList } from '@/hooks/useRequests'
import { formatDate } from '@/lib/money'
import { folioNumber } from '@/lib/outcome'

/** Recorre los pendientes con J (siguiente) y K (anterior), salvo mientras se escribe. */
function usePendingNavigation(currentId: string | undefined) {
  const navigate = useNavigate()
  const { data } = useRequestList()
  const pending = useMemo(
    () =>
      (data ?? [])
        .filter((r) => r.outcome === 'PENDING_APPROVAL')
        .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
        .map((r) => r.id),
    [data],
  )
  const index = currentId ? pending.indexOf(currentId) : -1
  const others = pending.filter((id) => id !== currentId)
  const next = index >= 0 ? pending[(index + 1) % pending.length] : others[0]
  const prev = index >= 0 ? pending[(index - 1 + pending.length) % pending.length] : others[others.length - 1]
  const hasOthers = others.length > 0

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement
      if (target.closest('input, textarea, select, [contenteditable="true"]') || e.metaKey || e.ctrlKey || e.altKey) return
      if (!hasOthers) return
      if (e.key === 'j' && next) navigate(`/requests/${next}`)
      if (e.key === 'k' && prev) navigate(`/requests/${prev}`)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [hasOthers, next, prev, navigate])

  return { count: others.length, next: hasOthers ? next : undefined, prev: hasOthers ? prev : undefined }
}

export function RequestDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: detail, isPending, isError, error, refetch } = useRequestDetail(id)
  const pendingNav = usePendingNavigation(id)
  const [freshStamp, setFreshStamp] = useState(false)

  useEffect(() => setFreshStamp(false), [id])

  if (isPending) {
    return (
      <div className="mx-auto max-w-[88rem] space-y-4 px-4 pt-6 sm:px-6">
        <Skeleton className="bg-paper h-16 w-full" />
        <Skeleton className="bg-paper h-[28rem] w-full" />
      </div>
    )
  }

  if (isError || !detail) {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center">
        <p className="font-semibold">No se pudo abrir esta solicitud.</p>
        <p className="text-ink-soft mt-1 text-sm">
          {error instanceof Error ? error.message : `No existe la solicitud ${id}.`}
        </p>
        <div className="mt-4 flex justify-center gap-2">
          <button
            type="button"
            onClick={() => refetch()}
            className="border-rule-strong hover:bg-paper h-8 rounded-md border px-3 text-sm font-medium"
          >
            Reintentar
          </button>
          <Link to="/" className="bg-ink text-paper inline-flex h-8 items-center rounded-md px-3 text-sm font-semibold">
            Volver a la bandeja
          </Link>
        </div>
      </div>
    )
  }

  const pending = detail.outcome === 'PENDING_APPROVAL'

  return (
    <div className="mx-auto max-w-[88rem] px-4 pt-5 pb-16 sm:px-6">
      <nav aria-label="Navegación de folios" className="flex flex-wrap items-center justify-between gap-2">
        <Link to="/" className="text-ink-soft hover:text-ink inline-flex items-center gap-1 text-sm font-medium">
          <ArrowLeft aria-hidden className="size-4" />
          Bandeja
        </Link>
        {pendingNav.count > 0 && (
          <div className="text-ink-soft flex items-center gap-1 text-xs">
            <span className="mr-1 hidden sm:inline">
              {pendingNav.count} {pendingNav.count === 1 ? 'otro pendiente' : 'otros pendientes'}
            </span>
            <Link
              to={`/requests/${pendingNav.prev}`}
              aria-label="Pendiente anterior (K)"
              className="border-rule-strong hover:bg-paper inline-flex h-7 items-center gap-1 rounded-md border px-2 font-medium"
            >
              <ChevronLeft aria-hidden className="size-3.5" />
              <kbd className="font-figures">K</kbd>
            </Link>
            <Link
              to={`/requests/${pendingNav.next}`}
              aria-label="Siguiente pendiente (J)"
              className="border-rule-strong hover:bg-paper inline-flex h-7 items-center gap-1 rounded-md border px-2 font-medium"
            >
              <kbd className="font-figures">J</kbd>
              <ChevronRight aria-hidden className="size-3.5" />
            </Link>
          </div>
        )}
      </nav>

      <article className="bg-paper border-rule-strong mt-3 rounded-md border">
        <header className="border-rule-strong flex flex-wrap items-start justify-between gap-x-6 gap-y-3 border-b px-5 pt-4 pb-3.5">
          <div className="min-w-0">
            <p className="font-figures text-ink-soft text-xs">Folio Nº {folioNumber(detail.id)}</p>
            <h1 className="type-title mt-0.5 truncate">
              {detail.customer_name || 'Cliente no registrado'}
            </h1>
            <p className="text-ink-soft mt-1 text-xs">
              <span className="font-figures">{detail.customer_id}</span>
              {' · '}registrada {formatDate(detail.created_at)}
              {detail.updated_at !== detail.created_at && <> · actualizada {formatDate(detail.updated_at)}</>}
            </p>
          </div>
          <OutcomeBadge outcome={detail.outcome} size="lg" />
        </header>

        <div className="grid grid-cols-[minmax(0,1fr)] lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="order-2 min-w-0 space-y-6 px-4 py-5 sm:px-5 lg:order-1">
            <section aria-labelledby="raw-title">
              <h2 id="raw-title" className="field-label">
                Lo que escribió el cliente
              </h2>
              <blockquote className="bg-paper-ruled mt-2 max-w-[70ch] rounded-sm px-4 py-3 text-base leading-relaxed">
                {detail.raw_text}
              </blockquote>
              {!detail.customer_name && (
                <p className="text-canary-ink mt-1.5 text-xs font-semibold">
                  {detail.customer_id} no está en el padrón: se cotizó con el nivel más conservador.
                </p>
              )}
            </section>

            <StageStrip events={detail.audit_trail} outcome={detail.outcome} />

            <ReasonsCard
              approvalReasons={detail.approval_reasons}
              rejectionReason={detail.rejection_reason}
              blockingReason={detail.blocking_reason}
            />

            <ExtractionCard extraction={detail.extraction} />

            {detail.quote && (
              <QuoteCard
                quote={detail.quote}
                decision={pending ? null : detail.human_decision}
                freshStamp={freshStamp}
              />
            )}

            {detail.outcome === 'DRAFT_READY' && detail.draft_text && <DraftCard draftText={detail.draft_text} />}

            <AuditTrailCard events={detail.audit_trail} />
          </div>

          <aside className="border-rule-strong order-1 min-w-0 border-b px-4 py-5 sm:px-5 lg:order-2 lg:border-b-0 lg:border-l">
            <div className="lg:sticky lg:top-16">
              {pending ? (
                <DecisionPanel
                  key={detail.id}
                  requestId={detail.id}
                  lastDecision={detail.human_decision}
                  approvalReasons={detail.approval_reasons}
                  onDecided={() => setFreshStamp(true)}
                />
              ) : (
                <OutcomePanel outcome={detail.outcome} decision={detail.human_decision} freshStamp={freshStamp} />
              )}
            </div>
          </aside>
        </div>
      </article>
    </div>
  )
}
