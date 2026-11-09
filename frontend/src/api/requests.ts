/**
 * Superficie única que usan los hooks de datos (`src/hooks/*`). Detrás de
 * ella hay dos implementaciones intercambiables del mismo contrato
 * (RF-01..RF-04, `docs/API_CONTRACT.md`):
 *
 *   - `mock` (por defecto): `src/mocks/store.ts`, en el navegador.
 *   - `http`: `src/api/client.ts`, contra `app/api/` real.
 *
 * Ningún componente de `src/features` importa `client.ts` ni `mocks/*`
 * directamente -- todos pasan por aquí, así que cambiar `VITE_API_MODE` no
 * toca una sola línea de UI.
 */

import { createRequestHttp, getRequestHttp, listRequestsHttp, submitDecisionHttp } from '@/api/client'
import { API_MODE } from '@/lib/config'
import { createRequest, getRequest, listRequests, submitDecision } from '@/mocks/store'
import type { CreateRequestBody, DecisionBody, RequestDetail, RequestListResponse } from '@/types/api'

/** Latencia simulada en modo mock: sin esto toda la UI resuelve en 0ms y
 * los estados de carga (skeletons, botones deshabilitados) nunca se ven,
 * lo que oculta bugs que sí importarían contra la API real. */
function simulatedLatency(): Promise<void> {
  const ms = 250 + Math.round(Math.random() * 300)
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export class NotFoundError extends Error {
  constructor(message = 'La solicitud no existe.') {
    super(message)
    this.name = 'NotFoundError'
  }
}

export async function apiCreateRequest(body: CreateRequestBody): Promise<RequestDetail> {
  if (API_MODE === 'http') return createRequestHttp(body)
  await simulatedLatency()
  return createRequest(body.customer_id, body.raw_text)
}

export async function apiListRequests(): Promise<RequestListResponse> {
  if (API_MODE === 'http') return listRequestsHttp()
  await simulatedLatency()
  return listRequests()
}

export async function apiGetRequest(id: string): Promise<RequestDetail> {
  if (API_MODE === 'http') return getRequestHttp(id)
  await simulatedLatency()
  const detail = getRequest(id)
  if (!detail) throw new NotFoundError(`No se encontró la solicitud ${id}.`)
  return detail
}

export async function apiSubmitDecision(id: string, body: DecisionBody): Promise<RequestDetail> {
  if (API_MODE === 'http') return submitDecisionHttp(id, body)
  await simulatedLatency()
  const result = submitDecision(id, body.decision_id, body.action, body.actor, body.comment)
  if (!result.ok) {
    if (result.error === 'not_found') throw new NotFoundError(`No se encontró la solicitud ${id}.`)
    if (result.error === 'conflict') {
      throw new Error(
        'La decisión contradice el estado actual de la solicitud y no se aplicó. Recarga la solicitud para ver el resultado vigente.',
      )
    }
    throw new Error(`Acción de decisión inválida: ${body.action}`)
  }
  return result.detail
}
