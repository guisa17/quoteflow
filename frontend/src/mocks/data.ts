/**
 * Seed de dominio para el motor mock. **No es una copia:** se importa directo
 * de `backend/app/data/*.json` (alias `@seed`, ver `vite.config.ts`), el
 * mismo archivo que lee el backend (ADR-001). Si el seed cambia, el backend y
 * la demo cambian juntos; no pueden desincronizarse.
 *
 * Los montos y porcentajes llegan del JSON como numeros (`45.00` -> 45). Se
 * convierten a strings decimales con la misma escala que conserva el backend
 * al leerlos como `Decimal` (dinero a 2 decimales, porcentajes a 1), y una
 * cifra con mas decimales de los admitidos detiene la carga en vez de
 * redondearse en silencio.
 */

import customersSeed from '@seed/customers.json'
import inventorySeed from '@seed/inventory.json'
import policySeed from '@seed/policies.json'
import productsSeed from '@seed/products.json'
import scenariosSeed from '@seed/sample_requests.json'
import type { Outcome, ReasonCode } from '@/types/api'

export type Tier = 'GOLD' | 'SILVER' | 'STANDARD'

export interface MockCustomer {
  customer_id: string
  legal_name: string
  tier: Tier
  country: string
  sites: string[]
  payment_terms_days: number
  active: boolean
}

export interface MockProduct {
  sku: string
  name: string
  category: string
  unit: string
  list_price_usd: string // decimal string; ver src/lib/money.ts
  lead_time_days: number
  active: boolean
}

export interface MockInventoryRecord {
  sku: string
  warehouse: string
  on_hand: number
  reserved: number
}

export interface MockPolicy {
  policy_version: string
  currency: string
  quote_validity_days: number
  discount_by_tier: Record<Tier, { max_discount_pct: string }>
  hard_discount_ceiling_pct: string
  approval_threshold_usd: string
  unknown_customer_requires_review: boolean
  tax: {
    name: string
    rate: string // "0.18"
    applies_to: string
    counts_toward_approval_threshold: boolean
  }
}

/** Numero del seed -> string decimal con `places` decimales, exacto. */
function decimal(value: number, places: number, field: string): string {
  const text = value.toFixed(places)
  if (Number(text) !== value) {
    throw new Error(`Seed: ${field} = ${value} tiene mas de ${places} decimales.`)
  }
  return text
}

const money = (value: number, field: string) => decimal(value, 2, field)
const pct = (value: number, field: string) => decimal(value, 1, field)

export const CUSTOMERS: MockCustomer[] = customersSeed.map((c) => ({
  ...c,
  tier: c.tier as Tier,
}))

export const PRODUCTS: MockProduct[] = productsSeed.map((p) => ({
  ...p,
  list_price_usd: money(p.list_price_usd, `${p.sku}.list_price_usd`),
}))

export const INVENTORY: MockInventoryRecord[] = inventorySeed

const tierPolicy = (tier: Tier) => ({
  max_discount_pct: pct(policySeed.discount_by_tier[tier].max_discount_pct, `${tier}.max_discount_pct`),
})

export const POLICY: MockPolicy = {
  policy_version: policySeed.policy_version,
  currency: policySeed.currency,
  quote_validity_days: policySeed.quote_validity_days,
  discount_by_tier: {
    GOLD: tierPolicy('GOLD'),
    SILVER: tierPolicy('SILVER'),
    STANDARD: tierPolicy('STANDARD'),
  },
  hard_discount_ceiling_pct: pct(policySeed.hard_discount_ceiling_pct, 'hard_discount_ceiling_pct'),
  approval_threshold_usd: money(policySeed.approval_threshold_usd, 'approval_threshold_usd'),
  unknown_customer_requires_review: policySeed.unknown_customer_requires_review,
  tax: {
    ...policySeed.tax,
    rate: String(policySeed.tax.rate),
  },
}

/** Los escenarios de `backend/app/data/sample_requests.json`: pueblan la
 * bandeja al primer arranque (`src/mocks/store.ts`) y, con su resultado
 * esperado, sostienen la prueba de paridad con el backend. */
export interface Scenario {
  id: string
  title: string
  customer_id: string
  raw_text: string
  expected_outcome: Outcome
  expected_reason: ReasonCode | null
}

export const SCENARIOS: Scenario[] = scenariosSeed.map((s) => ({
  id: s.id,
  title: s.title,
  customer_id: s.customer_id,
  raw_text: s.raw_text,
  expected_outcome: s.expected_outcome as Outcome,
  expected_reason: s.expected_reason as ReasonCode | null,
}))
