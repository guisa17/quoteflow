import { AlertTriangle } from 'lucide-react'
import { useParams } from 'react-router'

import { EmptyState } from '@/components/EmptyState'
import { PageBody, PageHeader } from '@/components/layout/PageHeader'
import { OutcomeBadge } from '@/components/OutcomeBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AuditTrailCard } from '@/features/request-detail/components/AuditTrailCard'
import { DecisionPanel } from '@/features/request-detail/components/DecisionPanel'
import { DraftCard } from '@/features/request-detail/components/DraftCard'
import { ExtractionCard } from '@/features/request-detail/components/ExtractionCard'
import { QuoteCard } from '@/features/request-detail/components/QuoteCard'
import { ReasonsCard } from '@/features/request-detail/components/ReasonsCard'
import { useRequestDetail } from '@/hooks/useRequests'
import { formatDate } from '@/lib/money'

function DetailSkeleton() {
  return (
    <PageBody className="max-w-4xl">
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-40 w-full" />
      <Skeleton className="h-40 w-full" />
    </PageBody>
  )
}

export function RequestDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: detail, isPending, isError, error, refetch } = useRequestDetail(id)

  if (isPending) return <DetailSkeleton />

  if (isError || !detail) {
    return (
      <PageBody className="max-w-4xl">
        <EmptyState
          icon={AlertTriangle}
          title="No se pudo cargar la solicitud"
          description={error instanceof Error ? error.message : `No existe la solicitud ${id}.`}
          action={
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              Reintentar
            </Button>
          }
        />
      </PageBody>
    )
  }

  return (
    <>
      <PageHeader
        title={detail.customer_name || detail.customer_id}
        breadcrumbs={[{ label: 'Bandeja', to: '/' }]}
        actions={<OutcomeBadge outcome={detail.outcome} />}
        description={`Solicitud ${detail.id} · registrada ${formatDate(detail.created_at)} · actualizada ${formatDate(detail.updated_at)}`}
      />
      <PageBody className="max-w-4xl">
        <Card>
          <CardContent className="space-y-2">
            <div className="flex flex-wrap items-baseline justify-between gap-2 text-xs">
              <span className="text-muted-foreground">
                Cliente: <span className="font-figures text-foreground">{detail.customer_id}</span>
                {!detail.customer_name && (
                  <span className="text-warning ml-2">no registrado en el padrón (BR-08)</span>
                )}
              </span>
              <span className="text-muted-foreground font-figures">thread {detail.thread_id}</span>
            </div>
            <blockquote className="border-border bg-muted/40 rounded-md border-l-2 px-3 py-2 text-sm italic">
              "{detail.raw_text}"
            </blockquote>
          </CardContent>
        </Card>

        <ExtractionCard extraction={detail.extraction} />

        {detail.quote && <QuoteCard quote={detail.quote} />}

        <ReasonsCard
          approvalReasons={detail.approval_reasons}
          rejectionReason={detail.rejection_reason}
          blockingReason={detail.blocking_reason}
        />

        {detail.outcome === 'PENDING_APPROVAL' && (
          <DecisionPanel requestId={detail.id} lastDecision={detail.human_decision} />
        )}

        {detail.outcome === 'DRAFT_READY' && detail.draft_text && (
          <DraftCard draftText={detail.draft_text} />
        )}

        <AuditTrailCard events={detail.audit_trail} />
      </PageBody>
    </>
  )
}
