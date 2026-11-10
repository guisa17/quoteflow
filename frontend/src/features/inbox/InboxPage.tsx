import { ArrowRight, CircleCheckBig, Plus, RotateCcw, Search, Stamp, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'

import { OutcomeBadge } from '@/components/OutcomeBadge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useRequestList } from '@/hooks/useRequests'
import { API_MODE } from '@/lib/config'
import { formatDate } from '@/lib/money'
import { OUTCOME_META, OUTCOME_ORDER, REASON_LABELS, TINT_CLASSES, folioNumber } from '@/lib/outcome'
import { ACTION_PAST, clearRecentDecisions, readRecentDecisions } from '@/lib/recentDecisions'
import { cn } from '@/lib/utils'
import type { DecisionAction, Outcome, RequestSummary } from '@/types/api'

/** Dos vistas, como en las bandejas de aprobación habituales: la cola de
 * trabajo (lo que espera tu decisión) y el archivo completo. Lo que decides
 * sale de la cola; el estado se filtra aparte, junto al buscador. */
type View = 'pending' | 'all'

const VIEW_PARAM: Record<View, string> = { pending: 'por-decidir', all: 'todas' }

const ACTION_VERB: Record<DecisionAction, string> = {
  APPROVE: 'Aprobaste',
  REJECT: 'Rechazaste',
  OBSERVE: 'Observaste',
}

/** El aviso de "acabas de decidir" solo tiene sentido justo después. */
const FRESH_WINDOW_MS = 15 * 60 * 1000

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

function parseStatus(value: string | null): Outcome | null {
  return value && (OUTCOME_ORDER as string[]).includes(value) ? (value as Outcome) : null
}

export function InboxPage() {
  const navigate = useNavigate()
  const { data, isPending, isError, error, refetch } = useRequestList()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [recent, setRecent] = useState(readRecentDecisions)
  const [bannerDismissed, setBannerDismissed] = useState(false)
  const freshRowRef = useRef<HTMLTableRowElement>(null)

  const counts = useMemo(() => {
    const result = Object.fromEntries(OUTCOME_ORDER.map((o) => [o, 0])) as Record<Outcome, number>
    for (const r of data ?? []) result[r.outcome] += 1
    return result
  }, [data])
  const total = data?.length ?? 0
  const pendingCount = counts.PENDING_APPROVAL

  // La vista vive en la URL: el botón Atrás y los enlaces la conservan.
  // Sin elección explícita, abre la cola si hay algo por decidir.
  const status = parseStatus(params.get('estado'))
  const viewParam = params.get('vista')
  const view: View =
    status || viewParam === VIEW_PARAM.all
      ? 'all'
      : viewParam === VIEW_PARAM.pending || isPending || pendingCount > 0
        ? 'pending'
        : 'all'

  function setView(next: View) {
    setParams({ vista: VIEW_PARAM[next] }, { replace: true })
  }
  function setStatus(next: Outcome | null) {
    setParams(next ? { vista: VIEW_PARAM.all, estado: next } : { vista: VIEW_PARAM.all }, { replace: true })
  }

  const rows = useMemo(
    () =>
      (data ?? [])
        .filter((r) =>
          view === 'pending' ? r.outcome === 'PENDING_APPROVAL' : status === null || r.outcome === status,
        )
        .filter((r) => matches(r, query))
        .sort(byAttention),
    [data, query, view, status],
  )

  const decidedById = useMemo(() => new Map(recent.map((d) => [d.requestId, d])), [recent])
  const latest = recent[0] && Date.now() - recent[0].at < FRESH_WINDOW_MS ? recent[0] : undefined
  const latestRequest = latest ? data?.find((r) => r.id === latest.requestId) : undefined
  const latestVisible = latestRequest ? rows.some((r) => r.id === latestRequest.id) : false

  // Al volver de decidir, o al pasar a "Todas", lleva la vista a la fila.
  useEffect(() => {
    freshRowRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [rows, latest?.requestId])

  async function handleReset() {
    const { resetDemoData } = await import('@/mocks/store')
    resetDemoData()
    clearRecentDecisions()
    setRecent([])
    setQuery('')
    setParams({}, { replace: true })
    await refetch()
  }

  function clearFilters() {
    setQuery('')
    setStatus(null)
  }

  return (
    <div className="mx-auto max-w-[88rem] px-4 pt-8 pb-16 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div>
          <h1 className="type-title">Bandeja</h1>
          <p className="text-ink-soft mt-1.5 text-sm">
            {isPending
              ? 'Cargando folios…'
              : pendingCount > 0
                ? `${pendingCount} ${pendingCount === 1 ? 'solicitud espera' : 'solicitudes esperan'} tu decisión.`
                : 'Estás al día: nada espera tu decisión.'}
          </p>
        </div>
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

      {latest && latestRequest && !bannerDismissed && (
        <div
          role="status"
          className="border-rule bg-paper shadow-card mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border py-2 pr-2 pl-2"
        >
          <span className="bg-lilac text-lilac-ink flex size-8 shrink-0 items-center justify-center rounded-md">
            <Stamp aria-hidden className="size-4 stroke-[2.25]" />
          </span>
          <p className="min-w-0 flex-1 text-sm">
            <span className="font-semibold">
              {ACTION_VERB[latest.action]} el folio{' '}
              <span className="font-figures">Nº {folioNumber(latest.requestId)}</span>
            </span>{' '}
            de {latestRequest.customer_name || latestRequest.customer_id} · ahora está en{' '}
            <span className={cn('font-semibold', TINT_CLASSES[OUTCOME_META[latestRequest.outcome].tint].ink)}>
              {OUTCOME_META[latestRequest.outcome].label}
            </span>
            .
            {view === 'pending' && pendingCount > 0 && latestRequest.outcome !== 'PENDING_APPROVAL' && (
              <span className="text-ink-soft">
                {' '}
                Te {pendingCount === 1 ? 'queda' : 'quedan'} {pendingCount} por decidir.
              </span>
            )}
          </p>
          <div className="flex items-center gap-1">
            {!latestVisible && (
              <button
                type="button"
                onClick={() => {
                  setQuery('')
                  setStatus(null)
                }}
                className="border-rule-strong hover:bg-paper-ruled inline-flex h-8 items-center gap-1 rounded-md border px-3 text-xs font-medium transition-colors"
              >
                Ver en Todas
              </button>
            )}
            <Link
              to={`/requests/${latest.requestId}`}
              className="bg-ink text-paper inline-flex h-8 items-center gap-1 rounded-md px-3 text-xs font-medium transition-opacity hover:opacity-85"
            >
              Abrir folio <ArrowRight aria-hidden className="size-3.5" />
            </Link>
            <button
              type="button"
              onClick={() => setBannerDismissed(true)}
              aria-label="Cerrar aviso"
              className="text-ink-soft hover:text-ink hover:bg-paper-ruled flex size-8 items-center justify-center rounded-md transition-colors"
            >
              <X aria-hidden className="size-4" />
            </button>
          </div>
        </div>
      )}

      <div className="bg-paper border-rule shadow-card mt-6 overflow-hidden rounded-xl border">
        {/* Vistas a la izquierda; búsqueda y estado a la derecha. */}
        <div className="border-rule flex flex-wrap items-end justify-between gap-x-4 gap-y-2 border-b px-2 pt-1 sm:px-3">
          <div role="tablist" aria-label="Vistas de la bandeja" className="flex">
            <ViewTab
              active={view === 'pending'}
              onClick={() => setView('pending')}
              label="Por decidir"
              count={isPending ? null : pendingCount}
              emphasize={pendingCount > 0}
            />
            <ViewTab
              active={view === 'all'}
              onClick={() => setView('all')}
              label="Todas"
              count={isPending ? null : total}
            />
          </div>

          <div className="flex w-full flex-wrap items-center gap-2 pb-2 sm:w-auto">
            {view === 'all' && (
              <div className="flex items-center gap-1">
                <Select
                  value={status ?? 'ALL'}
                  onValueChange={(v) => setStatus(v === 'ALL' ? null : (v as Outcome))}
                >
                  <SelectTrigger
                    aria-label="Filtrar por estado"
                    className={cn(
                      'h-9 w-auto min-w-[11rem] gap-2 rounded-md text-sm',
                      status && 'border-ink/40 font-semibold',
                    )}
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent align="end" className="min-w-[15rem]">
                    <SelectItem value="ALL" className="[&>span:last-child]:flex-1">
                      <span className="flex w-full items-center justify-between gap-4">
                        Todos los estados
                        <span className="font-figures text-ink-faint">{total}</span>
                      </span>
                    </SelectItem>
                    {OUTCOME_ORDER.map((o) => (
                      <SelectItem key={o} value={o} className="[&>span:last-child]:flex-1">
                        <span className="flex w-full items-center gap-2">
                          <span
                            aria-hidden
                            className={cn('size-2.5 shrink-0 rounded-full', TINT_CLASSES[OUTCOME_META[o].tint].dot)}
                          />
                          {OUTCOME_META[o].label}
                          <span className="font-figures text-ink-faint ml-auto pl-4">{counts[o]}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {status && (
                  <button
                    type="button"
                    onClick={() => setStatus(null)}
                    aria-label="Quitar filtro de estado"
                    title="Quitar filtro de estado"
                    className="text-ink-soft hover:text-ink hover:bg-paper-ruled flex size-9 items-center justify-center rounded-md transition-colors"
                  >
                    <X aria-hidden className="size-4" />
                  </button>
                )}
              </div>
            )}
            <label className="relative block min-w-0 flex-1 sm:flex-none">
              <span className="sr-only">Buscar solicitudes</span>
              <Search aria-hidden className="text-ink-faint absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Cliente, SKU o folio"
                className="border-rule-strong bg-paper placeholder:text-ink-faint focus-visible:border-stamp-blue h-9 w-full rounded-md border pr-2 pl-8 text-sm transition-colors outline-none sm:w-64"
              />
            </label>
          </div>
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
              className="border-rule-strong hover:bg-paper-ruled mt-4 h-9 rounded-md border px-3 text-sm font-medium"
            >
              Reintentar
            </button>
          </div>
        ) : rows.length === 0 ? (
          <EmptyState
            kind={
              total === 0
                ? 'no-data'
                : query.trim() || status
                  ? 'no-match'
                  : view === 'pending'
                    ? 'caught-up'
                    : 'no-data'
            }
            onClear={clearFilters}
            onShowAll={() => setView('all')}
          />
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
                  const fresh = r.id === latest?.requestId
                  return (
                    <tr
                      key={r.id}
                      ref={fresh ? freshRowRef : undefined}
                      onClick={() => navigate(href)}
                      aria-current={fresh ? 'true' : undefined}
                      className={cn(
                        'group border-rule cursor-pointer border-b transition-colors last:border-0',
                        fresh ? 'row-fresh' : 'hover:bg-paper-ruled',
                      )}
                    >
                      <td className="py-3 pl-4 align-top">
                        <Link
                          to={href}
                          onClick={(e) => e.stopPropagation()}
                          className="font-figures text-ink-soft group-hover:text-ink text-xs whitespace-nowrap focus-visible:outline-offset-4"
                        >
                          Nº {folioNumber(r.id)}
                        </Link>
                      </td>
                      <td className="py-3 pl-3 align-top">
                        <span className={cn('block leading-tight', pending ? 'font-bold' : 'font-medium')}>
                          {r.customer_name || 'Cliente no registrado'}
                        </span>
                        <span className="font-figures text-ink-faint text-xs">{r.customer_id}</span>
                      </td>
                      <td className="font-figures hidden py-3 pl-3 align-top md:table-cell">{r.summary}</td>
                      <td className="py-3 pl-3 align-top">
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
                      <td className="text-ink-soft hidden py-3 pl-3 align-top lg:table-cell">
                        {r.reason_code ? REASON_LABELS[r.reason_code] : '—'}
                      </td>
                      <td className="text-ink-soft hidden py-3 pr-4 pl-3 text-right align-top text-xs whitespace-nowrap sm:table-cell">
                        <span className="group-hover:hidden">{formatDate(r.updated_at)}</span>
                        <span className="text-ink hidden items-center justify-end gap-1 font-medium group-hover:inline-flex">
                          {pending ? 'Decidir' : 'Abrir'} <ArrowRight aria-hidden className="size-3.5" />
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

function ViewTab({
  active,
  onClick,
  label,
  count,
  emphasize = false,
}: {
  active: boolean
  onClick: () => void
  label: string
  count: number | null
  emphasize?: boolean
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={cn(
        'relative flex h-12 items-center gap-2 px-3 text-sm font-semibold transition-colors',
        'after:absolute after:inset-x-2 after:bottom-0 after:h-0.5 after:rounded-full after:transition-colors',
        active ? 'text-ink after:bg-ink' : 'text-ink-soft hover:text-ink after:bg-transparent',
      )}
    >
      {label}
      {count !== null && (
        <span
          className={cn(
            'font-figures inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-bold',
            emphasize ? 'bg-canary-mark text-[oklch(24%_0.06_70)]' : 'bg-paper-ruled text-ink-soft',
          )}
        >
          {count}
        </span>
      )}
    </button>
  )
}

function EmptyState({
  kind,
  onClear,
  onShowAll,
}: {
  kind: 'caught-up' | 'no-match' | 'no-data'
  onClear: () => void
  onShowAll: () => void
}) {
  const content = {
    'caught-up': {
      title: 'Nada por decidir',
      body: 'Las solicitudes que necesiten tu aprobación aparecerán aquí.',
    },
    'no-match': {
      title: 'Ningún folio coincide',
      body: 'Prueba con otro estado o borra la búsqueda.',
    },
    'no-data': {
      title: 'Todavía no hay solicitudes',
      body: 'Registra la primera y QuoteFlow la resolverá al instante.',
    },
  }[kind]

  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      {kind === 'caught-up' && <CircleCheckBig aria-hidden className="text-green-mark mb-3 size-8" />}
      <p className="font-semibold">{content.title}</p>
      <p className="text-ink-soft mt-1 text-sm">{content.body}</p>
      <div className="mt-4 flex gap-2">
        {kind === 'caught-up' && (
          <button
            type="button"
            onClick={onShowAll}
            className="border-rule-strong hover:bg-paper-ruled h-9 rounded-md border px-3 text-sm font-semibold"
          >
            Ver todas
          </button>
        )}
        {kind === 'no-match' && (
          <button
            type="button"
            onClick={onClear}
            className="bg-ink text-paper h-9 rounded-md px-3 text-sm font-semibold"
          >
            Quitar filtros
          </button>
        )}
        {kind !== 'no-match' && (
          <Link
            to="/new"
            className="bg-ink text-paper inline-flex h-9 items-center gap-1.5 rounded-md px-3 text-sm font-semibold"
          >
            <Plus aria-hidden className="size-4" /> Registrar solicitud
          </Link>
        )}
      </div>
    </div>
  )
}
