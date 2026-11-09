import { ArrowRight, Plus, RotateCcw, Search, Stamp, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { OutcomeBadge } from '@/components/OutcomeBadge'
import { Skeleton } from '@/components/ui/skeleton'
import { useRequestList } from '@/hooks/useRequests'
import { API_MODE } from '@/lib/config'
import { formatDate } from '@/lib/money'
import { OUTCOME_META, OUTCOME_ORDER, REASON_LABELS, TINT_CLASSES, folioNumber } from '@/lib/outcome'
import { ACTION_PAST, clearRecentDecisions, readRecentDecisions } from '@/lib/recentDecisions'
import { cn } from '@/lib/utils'
import type { DecisionAction, Outcome, RequestSummary } from '@/types/api'

const ACTION_VERB: Record<DecisionAction, string> = {
  APPROVE: 'Aprobaste',
  REJECT: 'Rechazaste',
  OBSERVE: 'Observaste',
}

/** El aviso de "acabas de decidir" solo tiene sentido justo después. */
const FRESH_WINDOW_MS = 15 * 60 * 1000

type Filter = Outcome | 'ALL'

function matches(request: RequestSummary, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return [request.customer_id, request.customer_name, request.summary, request.id].some((v) =>
    v.toLowerCase().includes(q),
  )
}

/** Primero lo que pide atención; dentro de cada resultado, lo más reciente. */
function byAttention(a: RequestSummary, b: RequestSummary): number {
  const rank = OUTCOME_ORDER.indexOf(a.outcome) - OUTCOME_ORDER.indexOf(b.outcome)
  return rank !== 0 ? rank : b.updated_at.localeCompare(a.updated_at)
}

export function InboxPage() {
  const navigate = useNavigate()
  const { data, isPending, isError, error, refetch } = useRequestList()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Filter>('ALL')
  const [recent, setRecent] = useState(readRecentDecisions)
  const [bannerDismissed, setBannerDismissed] = useState(false)
  const freshRowRef = useRef<HTMLTableRowElement>(null)

  const decidedById = useMemo(() => new Map(recent.map((d) => [d.requestId, d])), [recent])
  const latest = recent[0]
  const latestRequest = latest ? data?.find((r) => r.id === latest.requestId) : undefined
  const freshId = latest && Date.now() - latest.at < FRESH_WINDOW_MS ? latest.requestId : undefined

  // Al volver de decidir, lleva la vista a la fila: puede haber cambiado de grupo.
  useEffect(() => {
    freshRowRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [data, freshId])

  const counts = useMemo(() => {
    const result = Object.fromEntries(OUTCOME_ORDER.map((o) => [o, 0])) as Record<Outcome, number>
    for (const r of data ?? []) result[r.outcome] += 1
    return result
  }, [data])

  const rows = useMemo(
    () =>
      (data ?? [])
        .filter((r) => matches(r, query) && (filter === 'ALL' || r.outcome === filter))
        .sort(byAttention),
    [data, query, filter],
  )

  async function handleReset() {
    const { resetDemoData } = await import('@/mocks/store')
    resetDemoData()
    clearRecentDecisions()
    setRecent([])
    setFilter('ALL')
    setQuery('')
    await refetch()
  }

  const total = data?.length ?? 0

  return (
    <div className="mx-auto max-w-[88rem] px-4 pt-6 pb-16 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div>
          <h1 className="type-title">Bandeja</h1>
          <p className="text-ink-soft mt-1 text-sm">
            {isPending
              ? 'Cargando folios…'
              : counts.PENDING_APPROVAL > 0
                ? `${counts.PENDING_APPROVAL} ${counts.PENDING_APPROVAL === 1 ? 'solicitud espera' : 'solicitudes esperan'} tu decisión, de ${total} en total.`
                : `${total} solicitudes, ninguna espera decisión.`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {API_MODE === 'mock' && (
            <button
              type="button"
              onClick={handleReset}
              className="text-ink-soft hover:text-ink inline-flex h-8 items-center gap-1.5 rounded-md px-2 text-xs font-medium transition-colors"
            >
              <RotateCcw aria-hidden className="size-3.5" />
              Restaurar datos de demo
            </button>
          )}
        </div>
      </div>

      {latest && latestRequest && freshId && !bannerDismissed && (
        <div
          role="status"
          className="border-stamp-blue/40 bg-paper mt-5 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border py-2.5 pr-2 pl-3.5"
        >
          <Stamp aria-hidden className="text-stamp-blue size-4 shrink-0 stroke-[2.25]" />
          <p className="min-w-0 flex-1 text-sm">
            <span className="font-semibold">
              {ACTION_VERB[latest.action]} el folio <span className="font-figures">Nº {folioNumber(latest.requestId)}</span>
            </span>{' '}
            de {latestRequest.customer_name || latestRequest.customer_id}
            {' · '}ahora está en{' '}
            <span className={cn('font-semibold', TINT_CLASSES[OUTCOME_META[latestRequest.outcome].tint].ink)}>
              {OUTCOME_META[latestRequest.outcome].label}
            </span>{' '}
            y queda resaltado abajo.
          </p>
          <Link
            to={`/requests/${latest.requestId}`}
            className="text-stamp-blue hover:bg-stamp-blue/10 inline-flex h-7 items-center gap-1 rounded-full px-2.5 text-xs font-semibold transition-colors"
          >
            Abrir <ArrowRight aria-hidden className="size-3.5" />
          </Link>
          <button
            type="button"
            onClick={() => setBannerDismissed(true)}
            aria-label="Cerrar aviso"
            className="text-ink-soft hover:text-ink hover:bg-paper-ruled flex size-7 items-center justify-center rounded-full transition-colors"
          >
            <X aria-hidden className="size-4" />
          </button>
        </div>
      )}

      {/* Conteo por resultado: cada casilla filtra la bandeja. */}
      <div
        role="group"
        aria-label="Filtrar por resultado"
        className="bg-paper border-rule-strong mt-5 grid grid-cols-3 overflow-hidden rounded-xl border sm:grid-cols-6"
      >
        <TallyCell
          label="Todas"
          count={total}
          active={filter === 'ALL'}
          onClick={() => setFilter('ALL')}
          loading={isPending}
        />
        {OUTCOME_ORDER.map((outcome) => (
          <TallyCell
            key={outcome}
            label={OUTCOME_META[outcome].short}
            count={counts[outcome]}
            tint={OUTCOME_META[outcome].tint}
            active={filter === outcome}
            onClick={() => setFilter(filter === outcome ? 'ALL' : outcome)}
            loading={isPending}
          />
        ))}
      </div>

      <div className="bg-paper border-rule-strong mt-4 overflow-hidden rounded-xl border">
        <div className="border-rule flex flex-wrap items-center justify-between gap-3 border-b px-4 py-2.5">
          <p className="text-ink-soft text-xs">
            {filter === 'ALL' ? 'Todas las solicitudes' : OUTCOME_META[filter].label}
            {' · '}
            <span className="font-figures">{rows.length}</span> folio{rows.length === 1 ? '' : 's'}
          </p>
          <label className="relative block">
            <span className="sr-only">Buscar solicitudes</span>
            <Search aria-hidden className="text-ink-faint absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Cliente, SKU o folio"
              className="border-rule-strong bg-paper placeholder:text-ink-faint focus-visible:border-stamp-blue h-8 w-56 rounded-md border pr-2 pl-8 text-sm transition-colors outline-none sm:w-72"
            />
          </label>
        </div>

        {isPending ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="bg-paper-ruled h-9 w-full" />
            ))}
          </div>
        ) : isError ? (
          <div className="px-6 py-14 text-center">
            <p className="font-semibold">No se pudo cargar la bandeja.</p>
            <p className="text-ink-soft mt-1 text-sm">
              {error instanceof Error ? error.message : 'Error desconocido.'}
            </p>
            <button
              type="button"
              onClick={() => refetch()}
              className="border-rule-strong hover:bg-paper-ruled mt-4 h-8 rounded-md border px-3 text-sm font-medium"
            >
              Reintentar
            </button>
          </div>
        ) : rows.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <p className="font-semibold">
              {total > 0 ? 'Ningún folio coincide con el filtro.' : 'Todavía no hay solicitudes.'}
            </p>
            <p className="text-ink-soft mt-1 text-sm">
              {total > 0
                ? 'Prueba con otro resultado o borra la búsqueda.'
                : 'Registra la primera y QuoteFlow la resolverá al instante.'}
            </p>
            <Link
              to={total > 0 ? '/' : '/new'}
              onClick={() => {
                setFilter('ALL')
                setQuery('')
              }}
              className="bg-ink text-paper mt-4 inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-sm font-semibold"
            >
              {total > 0 ? 'Ver todas' : (
                <>
                  <Plus aria-hidden className="size-4" /> Registrar solicitud
                </>
              )}
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[22rem] text-left text-sm">
            <thead>
              <tr className="field-label border-rule border-b">
                <th scope="col" className="w-20 py-2 pl-4 font-semibold sm:w-24">Folio</th>
                <th scope="col" className="py-2 pl-3 font-semibold">Cliente</th>
                <th scope="col" className="hidden py-2 pl-3 font-semibold md:table-cell">Pedido</th>
                <th scope="col" className="py-2 pl-3 font-semibold">Resultado</th>
                <th scope="col" className="hidden py-2 pl-3 font-semibold lg:table-cell">Motivo</th>
                <th scope="col" className="hidden py-2 pr-4 pl-3 text-right font-semibold sm:table-cell">
                  Actualizado
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const pending = r.outcome === 'PENDING_APPROVAL'
                const href = `/requests/${r.id}`
                const decided = decidedById.get(r.id)
                const fresh = r.id === freshId
                return (
                  <tr
                    key={r.id}
                    ref={fresh ? freshRowRef : undefined}
                    onClick={() => navigate(href)}
                    aria-current={fresh ? 'true' : undefined}
                    className={cn(
                      'group border-rule cursor-pointer border-b transition-colors last:border-0',
                      fresh
                        ? 'row-fresh'
                        : pending
                          ? 'bg-canary/30 hover:bg-canary/55'
                          : 'hover:bg-paper-ruled',
                    )}
                  >
                    <td className="relative py-2.5 pl-4 align-top">
                      {/* Lomo de color: el resultado se ve antes de leer la fila. */}
                      <span
                        aria-hidden
                        className={cn(
                          'absolute inset-y-1.5 left-1 w-1 rounded-full',
                          TINT_CLASSES[OUTCOME_META[r.outcome].tint].dot,
                        )}
                      />
                      <Link
                        to={href}
                        onClick={(e) => e.stopPropagation()}
                        className="font-figures text-ink-soft group-hover:text-ink text-xs whitespace-nowrap focus-visible:outline-offset-4"
                      >
                        Nº {folioNumber(r.id)}
                      </Link>
                    </td>
                    <td className="py-2.5 pl-3 align-top">
                      <span className={cn('block leading-tight', pending ? 'font-bold' : 'font-medium')}>
                        {r.customer_name || 'Cliente no registrado'}
                      </span>
                      <span className="font-figures text-ink-faint text-xs">{r.customer_id}</span>
                    </td>
                    <td className="font-figures hidden py-2.5 pl-3 align-top md:table-cell">
                      {r.summary}
                    </td>
                    <td className="py-2.5 pl-3 align-top">
                      <OutcomeBadge outcome={r.outcome} />
                      {decided && (
                        <span
                          className={cn(
                            'mt-1 flex items-center gap-1 text-xs font-semibold',
                            fresh ? 'text-stamp-blue' : 'text-ink-soft',
                          )}
                        >
                          <Stamp aria-hidden className="size-3 stroke-[2.25]" />
                          {ACTION_PAST[decided.action]} por ti{fresh ? ' · recién' : ''}
                        </span>
                      )}
                    </td>
                    <td className="text-ink-soft hidden py-2.5 pl-3 align-top lg:table-cell">
                      {r.reason_code ? REASON_LABELS[r.reason_code] : '—'}
                    </td>
                    <td className="text-ink-soft hidden py-2.5 pr-4 pl-3 text-right align-top text-xs whitespace-nowrap sm:table-cell">
                      <span className="group-hover:hidden">{formatDate(r.updated_at)}</span>
                      <span className="text-ink hidden items-center justify-end gap-1 font-medium group-hover:inline-flex">
                        Abrir <ArrowRight aria-hidden className="size-3.5" />
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          </div>
        )}
      </div>
    </div>
  )
}

function TallyCell({
  label,
  count,
  tint,
  active,
  onClick,
  loading,
}: {
  label: string
  count: number
  tint?: keyof typeof TINT_CLASSES
  active: boolean
  onClick: () => void
  loading: boolean
}) {
  const t = tint ? TINT_CLASSES[tint] : null
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'border-rule relative flex flex-col items-start gap-1 border-r border-b px-4 pt-3 pb-2.5 text-left transition-colors sm:border-b-0 [&:nth-child(3n)]:border-r-0 sm:[&:nth-child(3n)]:border-r sm:last:border-r-0',
        active ? (t ? t.surface : 'bg-paper-ruled') : 'hover:bg-paper-ruled',
      )}
    >
      <span className={cn('flex items-center gap-1.5 text-xs font-semibold', t ? t.ink : 'text-ink-soft')}>
        {t && <span aria-hidden className={cn('size-2.5 rounded-full', t.dot)} />}
        {label}
      </span>
      <span className="font-figures text-[1.375rem] leading-none font-semibold">
        {loading ? '–' : count}
      </span>
      {active && <span aria-hidden className="bg-ink absolute inset-x-0 bottom-0 h-0.5" />}
    </button>
  )
}
