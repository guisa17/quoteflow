import type { Outcome, ReasonCode } from '@/types/api'
import type { BadgeProps } from '@/components/ui/badge'

/** Etiqueta y color semántico de cada uno de los cinco resultados
 * terminales (REQUIREMENTS.md §1, §3 RF-09). Un solo lugar para esta
 * traducción -- la bandeja y el detalle la comparten. */
export const OUTCOME_META: Record<
  Outcome,
  { label: string; variant: NonNullable<BadgeProps['variant']>; description: string }
> = {
  DRAFT_READY: {
    label: 'Borrador listo',
    variant: 'success',
    description: 'Cotización calculada dentro de política; borrador emitido.',
  },
  NEEDS_CLARIFICATION: {
    label: 'Necesita aclaración',
    variant: 'warning',
    description: 'Falta información esencial para poder cotizar (BR-10).',
  },
  PENDING_APPROVAL: {
    label: 'Pendiente de aprobación',
    variant: 'accent',
    description: 'Requiere una decisión humana antes de continuar (BR-05/06/08).',
  },
  BLOCKED: {
    label: 'Detenida',
    variant: 'destructive',
    description: 'SKU inexistente o stock insuficiente (BR-12/13).',
  },
  REJECTED_BY_POLICY: {
    label: 'Rechazada por política',
    variant: 'destructive',
    description: 'Descuento por encima del techo duro, o rechazo humano (BR-07/14).',
  },
}

export const REASON_LABELS: Record<ReasonCode, string> = {
  MISSING_PRODUCT_REFERENCE: 'Falta referencia de producto',
  MISSING_QUANTITY: 'Falta cantidad',
  UNKNOWN_SKU: 'SKU desconocido',
  INSUFFICIENT_STOCK: 'Stock insuficiente',
  THRESHOLD_EXCEEDED: 'Supera el umbral de aprobación',
  DISCOUNT_EXCEPTION: 'Excepción de descuento',
  UNKNOWN_CUSTOMER: 'Cliente desconocido',
  DISCOUNT_ABOVE_HARD_CEILING: 'Descuento sobre el techo duro',
  EXTRACTION_FAILED: 'Fallo de extracción',
}
