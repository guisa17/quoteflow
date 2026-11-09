/**
 * Aritmética decimal en centavos enteros, para el motor mock.
 *
 * Excepción deliberada a la regla "el frontend no hace aritmética con
 * montos": esa regla protege al *consumidor* de la API real, que solo debe
 * formatear los strings que el backend ya calculó (docs/API_CONTRACT.md).
 * Este módulo hace el papel del backend — es el puerto en TypeScript de
 * `backend/app/domain/pricing.py` (RF-06, BR-04) para que `npm run dev`
 * pueda producir una cotización completa sin `app/api/`. Fuera de
 * `src/mocks/`, ningún archivo debe importar esto.
 *
 * Se trabaja en centavos enteros (no `Decimal`, que no existe en JS) y se
 * redondea explícitamente ROUND_HALF_UP en cada paso monetario, igual que
 * `pricing.py` — nunca se deja que `toFixed` decida el redondeo de negocio.
 */

/** "45.00" -> 4500. Asume como máximo 2 decimales (forma del seed). */
export function toCents(decimal: string): number {
  const [whole, frac = ''] = decimal.trim().split('.')
  const cents = (frac + '00').slice(0, 2)
  const sign = whole.startsWith('-') ? -1 : 1
  const wholeAbs = whole.replace('-', '') || '0'
  return sign * (Number(wholeAbs) * 100 + Number(cents))
}

/** 4500 -> "45.00" */
export function fromCents(cents: number): string {
  const sign = cents < 0 ? '-' : ''
  const abs = Math.abs(Math.round(cents))
  const wholePart = Math.floor(abs / 100)
  const centPart = abs % 100
  return `${sign}${wholePart}.${String(centPart).padStart(2, '0')}`
}

/** ROUND_HALF_UP explícito (BR-04) — el default de JS para negativos no
 * aplica aquí porque todos los montos del dominio son >= 0. */
export function roundHalfUpCents(value: number): number {
  return Math.floor(value + 0.5)
}

/** subtotal_cents * pct / 100, redondeado a centavo (ROUND_HALF_UP). */
export function pctOfCents(amountCents: number, pctDecimalString: string): number {
  const pct = Number(pctDecimalString)
  return roundHalfUpCents((amountCents * pct) / 100)
}

export function sumCents(values: number[]): number {
  return values.reduce((acc, v) => acc + v, 0)
}
