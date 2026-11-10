/**
 * Puerto en TypeScript de `backend/app/llm/fake_extractor.py` (RF-10).
 *
 * Mismo principio, mismas reglas de texto: una referencia con forma XX-000,
 * el número más cercano que la precede como cantidad, el primer "N%" como
 * descuento solicitado, y "para (la|el) (planta|obra|proyecto) de <Sitio>"
 * como sede. No es un sustituto de un LLM real — es deliberadamente rígido,
 * como su contraparte de backend, y resuelve exactamente los 8 escenarios de
 * `sample_requests.json` más cualquier texto con la misma forma general.
 *
 * Deliberadamente no lee el catálogo ni el inventario (igual que el
 * original): que "ZZ-999" no exista es un problema que decide `resolveCatalog`
 * en `engine.ts`, no este módulo.
 */

import type { Extraction } from '@/types/api'

const SKU_RE = /\b[A-Za-z]{2}-\d{3}\b/g
// Un número seguido de "%" (entero o con decimales, con punto o coma) es un
// descuento, no una cantidad. Paridad con backend/app/llm/fake_extractor.py.
const NUMBER_RE = /\b\d+\b(?![\d.,]*\s*%)/g
const DISCOUNT_RE = /(\d+(?:[.,]\d+)?)\s*%/
const SITE_RE =
  /\bpara\s+(?:la\s+|el\s+)?(?:planta|obra|proyecto)?\s*(?:de\s+)?([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*)*)/

const QUANTITY_WINDOW_CHARS = 45

function quantityBefore(text: string, skuStart: number, previousSkuEnd: number): number | null {
  const windowStart = Math.max(previousSkuEnd, skuStart - QUANTITY_WINDOW_CHARS)
  const window = text.slice(windowStart, skuStart)
  const numbers = [...window.matchAll(NUMBER_RE)]
  if (numbers.length === 0) return null
  return Number(numbers[numbers.length - 1][0])
}

function extractSite(text: string): string | null {
  const match = SITE_RE.exec(text)
  if (match === null) return null
  return match[1].replace(/[.,]+$/, '')
}

function extractDiscount(text: string): string | null {
  const match = DISCOUNT_RE.exec(text)
  if (match === null) return null
  return match[1].replace(',', '.')
}

export function fakeExtract(rawText: string): Extraction {
  let previousSkuEnd = 0
  const items = [...rawText.matchAll(SKU_RE)].map((match) => {
    const item = {
      product_reference: match[0],
      quantity: quantityBefore(rawText, match.index, previousSkuEnd),
    }
    previousSkuEnd = match.index + match[0].length
    return item
  })

  return {
    items,
    site: extractSite(rawText),
    requested_date: null, // BR-11: no esencial; el heurístico no infiere fechas ISO de texto libre
    requested_discount_pct: extractDiscount(rawText),
  }
}
