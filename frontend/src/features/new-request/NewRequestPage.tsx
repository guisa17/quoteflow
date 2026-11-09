import { ArrowLeft, Loader2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useCreateRequest } from '@/hooks/useRequests'
import { API_MODE } from '@/lib/config'
import { OUTCOME_META } from '@/lib/outcome'
import { cn } from '@/lib/utils'
import { CUSTOMERS, SCENARIOS } from '@/mocks/data'

const OTHER_CUSTOMER = '__other__'
const MIN_TEXT = 10

/** Casos de ejemplo del seed, con el resultado que cada uno produce. */
const EXAMPLES: { id: string; label: string }[] = [
  { id: 'S1_estandar_gold', label: 'Pedido estándar' },
  { id: 'S2_incompleto_sin_cantidad', label: 'Falta la cantidad' },
  { id: 'S3_aprobacion_por_monto', label: 'Supera USD 10 000' },
  { id: 'S4_aprobacion_por_excepcion_descuento', label: 'Descuento fuera de nivel' },
  { id: 'S5_sin_stock', label: 'Sin stock' },
  { id: 'S6_producto_desconocido', label: 'SKU inexistente' },
  { id: 'S7_cliente_desconocido', label: 'Cliente nuevo' },
  { id: 'S8_inyeccion_de_prompt', label: 'Intento de manipulación' },
]

export function NewRequestPage() {
  const navigate = useNavigate()
  const createRequest = useCreateRequest()

  const [customerChoice, setCustomerChoice] = useState<string>(CUSTOMERS[0]?.customer_id ?? '')
  const [customCustomerId, setCustomCustomerId] = useState('')
  const [rawText, setRawText] = useState('')
  const [touched, setTouched] = useState(false)

  const customerId = customerChoice === OTHER_CUSTOMER ? customCustomerId.trim() : customerChoice
  const customerIdValid = customerId.length > 0
  const rawTextValid = rawText.trim().length >= MIN_TEXT

  function loadExample(id: string) {
    const scenario = SCENARIOS.find((s) => s.id === id)
    if (!scenario) return
    const known = CUSTOMERS.some((c) => c.customer_id === scenario.customer_id)
    setCustomerChoice(known ? scenario.customer_id : OTHER_CUSTOMER)
    setCustomCustomerId(known ? '' : scenario.customer_id)
    setRawText(scenario.raw_text)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setTouched(true)
    if (!customerIdValid || !rawTextValid) return
    try {
      const detail = await createRequest.mutateAsync({ customer_id: customerId, raw_text: rawText.trim() })
      toast.success(`Folio registrado: ${OUTCOME_META[detail.outcome].label}.`)
      navigate(`/requests/${detail.id}`)
    } catch (err) {
      toast.error('No se registró la solicitud', {
        description: err instanceof Error ? err.message : 'Error desconocido.',
      })
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 pt-5 pb-16 sm:px-6">
      <Link to="/" className="text-ink-soft hover:text-ink inline-flex items-center gap-1 text-sm font-medium">
        <ArrowLeft aria-hidden className="size-4" />
        Bandeja
      </Link>

      <form onSubmit={handleSubmit} noValidate className="bg-paper border-rule shadow-card mt-3 rounded-xl border">
        <header className="border-rule border-b px-5 pt-5 pb-4">
          <p className="field-label font-figures">// Folio Nº ——————</p>
          <h1 className="type-title mt-1.5">Nueva solicitud</h1>
          <p className="text-ink-soft mt-1 text-sm">
            Pega el pedido tal como llegó. QuoteFlow lo lee, consulta catálogo, stock y política, y lo resuelve al
            instante.
          </p>
        </header>

        <div className="space-y-5 px-5 py-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="customer-select" className="field-label">
                Cliente
              </label>
              <Select value={customerChoice} onValueChange={setCustomerChoice}>
                <SelectTrigger id="customer-select" className="bg-paper border-rule-strong mt-1 rounded-md">
                  <SelectValue placeholder="Elige un cliente" />
                </SelectTrigger>
                <SelectContent className="bg-paper border-rule-strong">
                  {CUSTOMERS.map((c) => (
                    <SelectItem key={c.customer_id} value={c.customer_id}>
                      {c.legal_name} · {c.tier}
                    </SelectItem>
                  ))}
                  <SelectItem value={OTHER_CUSTOMER}>Cliente no registrado…</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label htmlFor="customer-id" className="field-label">
                Código de cliente
              </label>
              <input
                id="customer-id"
                value={customerChoice === OTHER_CUSTOMER ? customCustomerId : customerId}
                readOnly={customerChoice !== OTHER_CUSTOMER}
                onChange={(e) => setCustomCustomerId(e.target.value)}
                maxLength={64}
                placeholder="FER-9999"
                aria-invalid={touched && !customerIdValid}
                className={cn(
                  'font-figures border-rule-strong mt-1 h-9 w-full rounded-md border px-3 text-sm outline-none',
                  customerChoice === OTHER_CUSTOMER ? 'bg-paper focus-visible:border-stamp-blue' : 'bg-paper-ruled text-ink-soft',
                  touched && !customerIdValid && 'border-stamp-red',
                )}
              />
              {touched && !customerIdValid && (
                <p className="text-red-ink mt-1 text-xs font-semibold">Escribe el código del cliente.</p>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="raw-text" className="field-label">
              Texto del pedido
            </label>
            <textarea
              id="raw-text"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              maxLength={10000}
              rows={6}
              aria-invalid={touched && !rawTextValid}
              placeholder="Necesito 20 cascos modelo HX-200 para la planta de Arequipa…"
              className={cn(
                'bg-paper border-rule-strong placeholder:text-ink-faint focus-visible:border-stamp-blue mt-1 w-full resize-y rounded-md border px-3 py-2.5 text-base leading-relaxed outline-none',
                touched && !rawTextValid && 'border-stamp-red',
              )}
            />
            <div className="mt-1 flex justify-between gap-4 text-xs">
              {touched && !rawTextValid ? (
                <p className="text-red-ink font-semibold">Describe el pedido con al menos {MIN_TEXT} caracteres.</p>
              ) : (
                <p className="text-ink-faint">
                  Las referencias de producto tienen la forma <span className="font-figures">HX-200</span>.
                </p>
              )}
              <span className="font-figures text-ink-faint">{rawText.length.toLocaleString('es-PE')}/10 000</span>
            </div>
          </div>

          <fieldset>
            <legend className="field-label">Probar con un caso de ejemplo</legend>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.id}
                  type="button"
                  onClick={() => loadExample(ex.id)}
                  className="border-rule-strong hover:bg-paper-ruled hover:border-ink-soft h-7 rounded-full border px-3 text-xs font-medium transition-colors"
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </fieldset>
        </div>

        <footer className="border-rule bg-paper-ruled flex flex-wrap items-center justify-between gap-3 rounded-b-xl border-t px-5 py-3">
          <p className="text-ink-soft text-xs">
            {API_MODE === 'mock'
              ? 'Demo: las reglas corren en tu navegador, con datos ficticios.'
              : 'Se procesa en el servidor y queda guardado.'}
          </p>
          <button
            type="submit"
            disabled={createRequest.isPending}
            className="bg-ink text-paper inline-flex h-10 items-center gap-2 rounded-md px-5 text-sm font-medium transition-opacity hover:opacity-85 disabled:opacity-50"
          >
            {createRequest.isPending && <Loader2 aria-hidden className="size-4 animate-spin" />}
            Registrar y resolver
          </button>
        </footer>
      </form>
    </div>
  )
}
