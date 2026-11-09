/**
 * Formato de montos decimales (string) para mostrar.
 *
 * El contrato (docs/API_CONTRACT.md) es explícito: los montos viajan como
 * `string` decimal y "el frontend formatea para mostrar; no hace aritmética
 * con estos valores". Estas funciones solo dan forma visual — separador de
 * miles, símbolo de moneda — nunca combinan dos montos entre sí.
 */

export function formatMoney(decimal: string, currency = 'USD'): string {
  const value = Number(decimal)
  if (Number.isNaN(value)) return decimal
  return new Intl.NumberFormat('es-PE', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/** Igual que `formatMoney` pero sin símbolo de moneda (para columnas donde
 * la moneda ya está indicada en la cabecera). */
export function formatAmount(decimal: string): string {
  const value = Number(decimal)
  if (Number.isNaN(value)) return decimal
  return new Intl.NumberFormat('es-PE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatPercent(decimal: string): string {
  const value = Number(decimal)
  if (Number.isNaN(value)) return `${decimal}%`
  return `${new Intl.NumberFormat('es-PE', { maximumFractionDigits: 2 }).format(value)}%`
}

export function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat('es-PE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
