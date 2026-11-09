import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiCreateRequest, apiGetRequest, apiListRequests, apiSubmitDecision } from '@/api/requests'
import type { CreateRequestBody, DecisionBody } from '@/types/api'

export const requestKeys = {
  all: ['requests'] as const,
  list: () => [...requestKeys.all, 'list'] as const,
  detail: (id: string) => [...requestKeys.all, 'detail', id] as const,
}

/** RF-02 — bandeja de solicitudes. */
export function useRequestList() {
  return useQuery({
    queryKey: requestKeys.list(),
    queryFn: apiListRequests,
  })
}

/** RF-03 — detalle con trazabilidad. */
export function useRequestDetail(id: string | undefined) {
  return useQuery({
    queryKey: requestKeys.detail(id ?? ''),
    queryFn: () => apiGetRequest(id as string),
    enabled: Boolean(id),
  })
}

/** RF-01 — crear solicitud. */
export function useCreateRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateRequestBody) => apiCreateRequest(body),
    onSuccess: (detail) => {
      queryClient.invalidateQueries({ queryKey: requestKeys.list() })
      queryClient.setQueryData(requestKeys.detail(detail.id), detail)
    },
  })
}

/** RF-04 — aprobar / rechazar / observar. */
export function useSubmitDecision(requestId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: DecisionBody) => apiSubmitDecision(requestId, body),
    onSuccess: (detail) => {
      queryClient.setQueryData(requestKeys.detail(requestId), detail)
      queryClient.invalidateQueries({ queryKey: requestKeys.list() })
    },
    // BR-19: si otra persona ya resolvió el caso, la pantalla debe mostrar el resultado vigente.
    onError: () => {
      queryClient.invalidateQueries({ queryKey: requestKeys.detail(requestId) })
      queryClient.invalidateQueries({ queryKey: requestKeys.list() })
    },
  })
}
