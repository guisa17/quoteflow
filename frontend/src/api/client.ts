/**
 * Cliente HTTP real contra `app/api/` (RF-01..RF-04), tal como lo define
 * `docs/API_CONTRACT.md`. Se selecciona con `VITE_API_MODE=http` (ver
 * `src/lib/config.ts`).
 */

import axios, { AxiosError } from 'axios'
import { API_BASE_URL } from '@/lib/config'
import type {
  ApiError,
  CreateRequestBody,
  DecisionBody,
  RequestDetail,
  RequestListResponse,
} from '@/types/api'

const http = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

/** El contrato no exige que el frontend interprete `detail` para decidir
 * nada (docs/API_CONTRACT.md § Errores) -- solo lo usa como mensaje. */
export class QuoteFlowApiError extends Error {
  status: number
  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'QuoteFlowApiError'
    this.status = status
  }
}

/** Un error de validación de FastAPI (`422`) trae `detail` como lista, no como
 * texto: se convierte a un mensaje legible en vez de mostrar `[object Object]`. */
function readableDetail(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((issue: { msg?: unknown }) => issue?.msg)
      .filter((msg): msg is string => typeof msg === 'string')
    if (messages.length > 0) return messages.join(' · ')
  }
  return fallback
}

function unwrap(error: unknown): never {
  if (error instanceof AxiosError) {
    const detail = readableDetail((error.response?.data as ApiError | undefined)?.detail, error.message)
    throw new QuoteFlowApiError(error.response?.status ?? 0, detail)
  }
  throw error
}

// RF-01
export async function createRequestHttp(body: CreateRequestBody): Promise<RequestDetail> {
  try {
    const { data } = await http.post<RequestDetail>('/requests', body)
    return data
  } catch (error) {
    unwrap(error)
  }
}

// RF-02
export async function listRequestsHttp(): Promise<RequestListResponse> {
  try {
    const { data } = await http.get<RequestListResponse>('/requests')
    return data
  } catch (error) {
    unwrap(error)
  }
}

// RF-03
export async function getRequestHttp(id: string): Promise<RequestDetail> {
  try {
    const { data } = await http.get<RequestDetail>(`/requests/${id}`)
    return data
  } catch (error) {
    unwrap(error)
  }
}

// RF-04
export async function submitDecisionHttp(id: string, body: DecisionBody): Promise<RequestDetail> {
  try {
    const { data } = await http.post<RequestDetail>(`/requests/${id}/decision`, body)
    return data
  } catch (error) {
    unwrap(error)
  }
}
