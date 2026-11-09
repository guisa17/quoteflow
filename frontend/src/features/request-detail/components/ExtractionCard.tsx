import { formatPercent } from '@/lib/money'
import type { Extraction } from '@/types/api'

/** Lo que el sistema entendió del texto, antes de consultar catálogo o
 * inventario. Mostrarlo aparte de la cotización hace visible que la lectura
 * solo interpreta: nunca pone precio ni stock (BR-01/BR-03). */
export function ExtractionCard({ extraction }: { extraction: Extraction | null }) {
  return (
    <section aria-labelledby="extraction-title">
      <h2 id="extraction-title" className="field-label">
        Lo que se entendió del texto
      </h2>
      {!extraction ? (
        <p className="bg-sky text-sky-ink mt-2 rounded-sm px-3 py-2 text-sm">
          La lectura falló dos veces y no produjo datos. No se cotizó nada.
        </p>
      ) : (
        <div className="border-rule-strong mt-2 grid grid-cols-2 overflow-hidden rounded-sm border sm:grid-cols-[minmax(0,2fr)_repeat(3,minmax(0,1fr))]">
          <Field label="Ítems" className="col-span-2 sm:col-span-1">
            {extraction.items.length === 0 ? (
              <span className="text-ink-soft">Ninguno identificado</span>
            ) : (
              <ul className="space-y-0.5">
                {extraction.items.map((item, i) => (
                  <li key={i} className="font-figures flex gap-2">
                    <span className={item.quantity === null ? 'text-red-ink font-semibold' : ''}>
                      {item.quantity ?? '¿?'} ×
                    </span>
                    <span>{item.product_reference}</span>
                  </li>
                ))}
              </ul>
            )}
          </Field>
          <Field label="Sede">{extraction.site ?? <Pending />}</Field>
          <Field label="Fecha">{extraction.requested_date ?? <Pending />}</Field>
          <Field label="Descuento pedido" className="col-span-2 sm:col-span-1">
            <span className="font-figures">
              {extraction.requested_discount_pct ? formatPercent(extraction.requested_discount_pct) : '0 %'}
            </span>
            {!extraction.requested_discount_pct && <span className="text-ink-faint ml-1.5 text-xs">no pedido</span>}
          </Field>
        </div>
      )}
    </section>
  )
}

function Field({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`border-rule border-r border-b px-3 pt-1.5 pb-2 last:border-r-0 sm:border-b-0 ${className}`}>
      <div className="field-label !text-[0.6875rem]">{label}</div>
      <div className="mt-0.5 text-sm font-medium">{children}</div>
    </div>
  )
}

function Pending() {
  return <span className="text-ink-faint font-normal">a confirmar</span>
}
