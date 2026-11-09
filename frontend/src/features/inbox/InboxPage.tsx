import { AlertTriangle, Inbox as InboxIcon, PlusCircle, RotateCcw, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { PageBody, PageHeader } from '@/components/layout/PageHeader'
import { OutcomeBadge } from '@/components/OutcomeBadge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useRequestList } from '@/hooks/useRequests'
import { API_MODE } from '@/lib/config'
import { formatDate } from '@/lib/money'
import { REASON_LABELS } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import type { Outcome, RequestSummary } from '@/types/api'

const OUTCOME_FILTERS: { value: Outcome | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'Todas' },
  { value: 'NEEDS_CLARIFICATION', label: 'Aclaración' },
  { value: 'PENDING_APPROVAL', label: 'Pendientes' },
  { value: 'DRAFT_READY', label: 'Listas' },
  { value: 'BLOCKED', label: 'Detenidas' },
  { value: 'REJECTED_BY_POLICY', label: 'Rechazadas' },
]

function matches(request: RequestSummary, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return (
    request.customer_id.toLowerCase().includes(q) ||
    request.customer_name.toLowerCase().includes(q) ||
    request.summary.toLowerCase().includes(q) ||
    request.id.toLowerCase().includes(q)
  )
}

export function InboxPage() {
  const { data, isPending, isError, error, refetch } = useRequestList()
  const [query, setQuery] = useState('')
  const [outcomeFilter, setOutcomeFilter] = useState<Outcome | 'ALL'>('ALL')

  const filtered = useMemo(() => {
    if (!data) return []
    return data.filter(
      (r) => matches(r, query) && (outcomeFilter === 'ALL' || r.outcome === outcomeFilter),
    )
  }, [data, query, outcomeFilter])

  async function handleReset() {
    // Solo existe en modo mock -- ver src/mocks/store.ts. No forma parte de
    // RF-09; es una comodidad de demo para volver a un estado conocido.
    const { resetDemoData } = await import('@/mocks/store')
    resetDemoData()
    await refetch()
  }

  return (
    <>
      <PageHeader
        title="Bandeja de solicitudes"
        description="Solicitudes de cotización registradas por el equipo comercial (RF-02)."
        actions={
          <>
            {API_MODE === 'mock' && (
              <Button variant="outline" size="sm" onClick={handleReset}>
                <RotateCcw aria-hidden />
                Reiniciar datos de demo
              </Button>
            )}
            <Button size="sm" asChild>
              <Link to="/new">
                <PlusCircle aria-hidden />
                Nueva solicitud
              </Link>
            </Button>
          </>
        }
      />
      <PageBody>
        <div className="bg-card border-border overflow-hidden rounded-xl border">
          <div className="border-border flex flex-wrap items-center justify-between gap-2 border-b px-3 py-2">
            <p className="text-muted-foreground text-xs font-medium tabular-nums">
              {isPending ? 'Cargando…' : `${filtered.length} solicitud${filtered.length === 1 ? '' : 'es'}`}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex flex-wrap items-center gap-1">
                {OUTCOME_FILTERS.map((f) => (
                  <button
                    key={f.value}
                    type="button"
                    onClick={() => setOutcomeFilter(f.value)}
                    className={cn(
                      'rounded-md border px-2 py-1 text-xs font-medium transition-colors',
                      outcomeFilter === f.value
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'border-input text-muted-foreground hover:text-foreground hover:bg-accent',
                    )}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
              <div className="relative">
                <Search
                  aria-hidden
                  className="text-muted-foreground absolute top-1/2 left-2 size-3.5 -translate-y-1/2"
                />
                <input
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Buscar cliente, resumen, id…"
                  aria-label="Buscar solicitudes"
                  className="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 h-8 w-48 rounded-md border pr-2 pl-7 text-xs transition-colors focus-visible:ring-2 focus-visible:outline-none sm:w-64"
                />
              </div>
            </div>
          </div>

          {isPending ? (
            <div className="space-y-2 p-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : isError ? (
            <EmptyState
              icon={AlertTriangle}
              title="No se pudo cargar la bandeja"
              description={error instanceof Error ? error.message : 'Error desconocido.'}
              action={
                <Button size="sm" variant="outline" onClick={() => refetch()}>
                  Reintentar
                </Button>
              }
            />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={InboxIcon}
              title="Sin resultados"
              description={
                data && data.length > 0
                  ? 'Ninguna solicitud coincide con el filtro actual.'
                  : 'Todavía no hay solicitudes registradas.'
              }
              action={
                <Button size="sm" asChild>
                  <Link to="/new">
                    <PlusCircle aria-hidden />
                    Registrar la primera
                  </Link>
                </Button>
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-muted-foreground border-border border-b text-xs">
                    <th className="px-3 py-2 font-medium">Cliente</th>
                    <th className="px-3 py-2 font-medium">Resumen</th>
                    <th className="px-3 py-2 font-medium">Resultado</th>
                    <th className="px-3 py-2 font-medium">Motivo</th>
                    <th className="px-3 py-2 font-medium">Actualizado</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((request) => (
                    <tr
                      key={request.id}
                      className="border-border hover:bg-accent/50 cursor-pointer border-b transition-colors last:border-0"
                    >
                      <td className="p-0">
                        <Link to={`/requests/${request.id}`} className="block px-3 py-2.5">
                          <span className="block font-medium">
                            {request.customer_name || request.customer_id}
                          </span>
                          {request.customer_name && (
                            <span className="text-muted-foreground font-figures block text-xs">
                              {request.customer_id}
                            </span>
                          )}
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link to={`/requests/${request.id}`} className="font-figures block px-3 py-2.5">
                          {request.summary}
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link to={`/requests/${request.id}`} className="block px-3 py-2.5">
                          <OutcomeBadge outcome={request.outcome} />
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link to={`/requests/${request.id}`} className="text-muted-foreground block px-3 py-2.5">
                          {request.reason_code ? REASON_LABELS[request.reason_code] : '—'}
                        </Link>
                      </td>
                      <td className="p-0">
                        <Link
                          to={`/requests/${request.id}`}
                          className="text-muted-foreground block px-3 py-2.5 whitespace-nowrap"
                        >
                          {formatDate(request.updated_at)}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </PageBody>
    </>
  )
}
