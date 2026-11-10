import { CircleCheck, CircleQuestionMark, CircleSlash, Clock3, OctagonX, type LucideIcon } from 'lucide-react'

import type { Outcome, ReasonCode } from '@/types/api'

export type Tint = 'canary' | 'violet' | 'green' | 'sky' | 'red'

/** Cada resultado se lee como una copia del talonario: un tinte de papel,
 * su tinta, un ícono y una etiqueta. El color nunca va solo. */
export const OUTCOME_META: Record<
  Outcome,
  { label: string; short: string; tint: Tint; icon: LucideIcon; description: string }
> = {
  PENDING_APPROVAL: {
    label: 'Pendiente de aprobación',
    short: 'Pendientes',
    tint: 'canary',
    icon: Clock3,
    description: 'Espera una decisión humana antes de continuar.',
  },
  NEEDS_CLARIFICATION: {
    label: 'Necesita aclaración',
    short: 'Aclaración',
    tint: 'sky',
    icon: CircleQuestionMark,
    description: 'Falta información esencial para poder cotizar.',
  },
  DRAFT_READY: {
    label: 'Borrador listo',
    short: 'Listas',
    tint: 'green',
    icon: CircleCheck,
    description: 'Cotización dentro de política, borrador preparado.',
  },
  BLOCKED: {
    label: 'Detenida',
    short: 'Detenidas',
    tint: 'violet',
    icon: CircleSlash,
    description: 'SKU inexistente o stock insuficiente.',
  },
  REJECTED_BY_POLICY: {
    label: 'Rechazada',
    short: 'Rechazadas',
    tint: 'red',
    icon: OctagonX,
    description: 'Descuento sobre el techo duro, o rechazo humano.',
  },
}

/** Orden de la bandeja: primero lo que pide atención. */
export const OUTCOME_ORDER: Outcome[] = [
  'PENDING_APPROVAL',
  'NEEDS_CLARIFICATION',
  'DRAFT_READY',
  'BLOCKED',
  'REJECTED_BY_POLICY',
]

export const TINT_CLASSES: Record<Tint, { surface: string; ink: string; dot: string }> = {
  canary: { surface: 'bg-canary', ink: 'text-canary-ink', dot: 'bg-canary-mark' },
  violet: { surface: 'bg-violet', ink: 'text-violet-ink', dot: 'bg-violet-mark' },
  green: { surface: 'bg-green', ink: 'text-green-ink', dot: 'bg-green-mark' },
  sky: { surface: 'bg-sky', ink: 'text-sky-ink', dot: 'bg-sky-mark' },
  red: { surface: 'bg-red', ink: 'text-red-ink', dot: 'bg-red-mark' },
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
  SUSPECTED_MANIPULATION: 'Posible manipulación en el texto',
}

/** Qué hacer a continuación, por resultado: la línea que el operador lee primero. */
export const NEXT_STEP: Record<Outcome, string> = {
  PENDING_APPROVAL: 'Revisa los motivos y decide: aprobar, rechazar u observar.',
  NEEDS_CLARIFICATION: 'Pide al cliente el dato que falta y registra una solicitud nueva.',
  DRAFT_READY: 'Revisa el borrador y envíalo por tu canal habitual. QuoteFlow no envía nada.',
  BLOCKED: 'Corrige el SKU o la cantidad con el cliente; no se cotizó nada parcialmente.',
  REJECTED_BY_POLICY: 'El caso está cerrado. Una nueva condición requiere una solicitud nueva.',
}

/** Número de folio mostrado: derivado del id, nunca inventado. */
export function folioNumber(id: string): string {
  const compact = id.replace(/[^a-zA-Z0-9]/g, '')
  return compact.slice(-6).toUpperCase()
}
