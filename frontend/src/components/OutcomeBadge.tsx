import { Badge } from '@/components/ui/badge'
import { OUTCOME_META } from '@/lib/outcome'
import type { Outcome } from '@/types/api'

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  const meta = OUTCOME_META[outcome]
  return <Badge variant={meta.variant}>{meta.label}</Badge>
}
