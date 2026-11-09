import { Loader2, SendHorizonal } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'

import { PageBody, PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useCreateRequest } from '@/hooks/useRequests'
import { CUSTOMERS } from '@/mocks/data'
import { OUTCOME_META } from '@/lib/outcome'
import { API_MODE } from '@/lib/config'

const OTHER_CUSTOMER = '__other__'

const EXAMPLE_TEXT =
  'Necesito 20 cascos modelo HX-200 para la planta de Arequipa. Somos clientes Gold. Requiero entrega la proxima semana y un 8% de descuento.'

export function NewRequestPage() {
  const navigate = useNavigate()
  const createRequest = useCreateRequest()

  const [customerChoice, setCustomerChoice] = useState<string>(CUSTOMERS[0]?.customer_id ?? '')
  const [customCustomerId, setCustomCustomerId] = useState('')
  const [rawText, setRawText] = useState('')
  const [touched, setTouched] = useState(false)

  const customerId = customerChoice === OTHER_CUSTOMER ? customCustomerId.trim() : customerChoice
  const customerIdValid = customerId.length > 0
  const rawTextValid = rawText.trim().length >= 10

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setTouched(true)
    if (!customerIdValid || !rawTextValid) return

    try {
      const detail = await createRequest.mutateAsync({
        customer_id: customerId,
        raw_text: rawText.trim(),
      })
      toast.success(`Solicitud registrada — ${OUTCOME_META[detail.outcome].label}`, {
        description: OUTCOME_META[detail.outcome].description,
      })
      navigate(`/requests/${detail.id}`)
    } catch (err) {
      toast.error('No se pudo registrar la solicitud', {
        description: err instanceof Error ? err.message : 'Error desconocido.',
      })
    }
  }

  return (
    <>
      <PageHeader
        title="Nueva solicitud"
        breadcrumbs={[{ label: 'Bandeja', to: '/' }]}
        description="RF-01 — customer_id + texto libre. El sistema resuelve el resultado al instante."
      />
      <PageBody className="max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle>Cliente</CardTitle>
              <CardDescription>
                Elige un cliente registrado, o "Otro" para probar el caso de cliente desconocido
                (BR-08).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="customer-select">Cliente</Label>
                <Select value={customerChoice} onValueChange={setCustomerChoice}>
                  <SelectTrigger id="customer-select">
                    <SelectValue placeholder="Selecciona un cliente" />
                  </SelectTrigger>
                  <SelectContent>
                    {CUSTOMERS.map((c) => (
                      <SelectItem key={c.customer_id} value={c.customer_id}>
                        {c.legal_name} · {c.customer_id} ({c.tier})
                      </SelectItem>
                    ))}
                    <SelectItem value={OTHER_CUSTOMER}>Otro (ingresar customer_id manualmente)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {customerChoice === OTHER_CUSTOMER && (
                <div className="space-y-1.5">
                  <Label htmlFor="customer-id">customer_id</Label>
                  <Input
                    id="customer-id"
                    value={customCustomerId}
                    onChange={(e) => setCustomCustomerId(e.target.value)}
                    maxLength={64}
                    placeholder="ej. FER-9999"
                    className="font-figures"
                  />
                </div>
              )}

              {touched && !customerIdValid && (
                <p className="text-destructive text-xs">Indica un customer_id.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Solicitud (texto libre)</CardTitle>
              <CardDescription>
                Describe lo que pide el cliente: producto, cantidad, sede, fecha y descuento si
                aplica. La extracción reconoce referencias con forma <span className="font-figures">XX-000</span> (ej.{' '}
                <span className="font-figures">HX-200</span>).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                maxLength={10000}
                placeholder={EXAMPLE_TEXT}
                rows={5}
                aria-label="Texto libre de la solicitud"
              />
              <div className="flex items-center justify-between">
                {touched && !rawTextValid ? (
                  <p className="text-destructive text-xs">Describe la solicitud con más detalle.</p>
                ) : (
                  <button
                    type="button"
                    onClick={() => setRawText(EXAMPLE_TEXT)}
                    className="text-primary-text text-xs hover:underline"
                  >
                    Usar texto de ejemplo (S1)
                  </button>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="flex items-center gap-3">
            <Button type="submit" disabled={createRequest.isPending}>
              {createRequest.isPending ? (
                <Loader2 aria-hidden className="animate-spin" />
              ) : (
                <SendHorizonal aria-hidden />
              )}
              Registrar solicitud
            </Button>
            {API_MODE === 'mock' && (
              <p className="text-muted-foreground text-xs">
                Modo demo: se resuelve con el motor de reglas del navegador, sin backend.
              </p>
            )}
          </div>
        </form>
      </PageBody>
    </>
  )
}
