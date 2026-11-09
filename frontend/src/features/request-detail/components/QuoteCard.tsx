import { Stamp } from '@/features/request-detail/components/Stamp'
import { formatAmount, formatMoney, formatPercent } from '@/lib/money'
import type { HumanDecision, Quote } from '@/types/api'

/** La cotización como cuerpo del formulario: líneas regladas y la caja de
 * totales. Los montos llegan calculados por el dominio y aquí solo se
 * formatean; ninguna suma ocurre en el navegador. El sello de la decisión
 * humana cae sobre la caja de totales. */
export function QuoteCard({
  quote,
  decision,
  freshStamp,
}: {
  quote: Quote
  decision: HumanDecision | null
  freshStamp: boolean
}) {
  return (
    <section aria-labelledby="quote-title">
      <h2 id="quote-title" className="field-label">
        Cotización
      </h2>
      <div className="border-rule-strong mt-2 overflow-hidden rounded-sm border">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-left text-sm">
            <thead>
              <tr className="field-label bg-paper-ruled border-rule-strong border-b !text-[0.625rem]">
                <th scope="col" className="py-1.5 pl-3 font-semibold">SKU</th>
                <th scope="col" className="py-1.5 pl-3 font-semibold">Descripción</th>
                <th scope="col" className="py-1.5 pl-3 text-right font-semibold">Cant.</th>
                <th scope="col" className="py-1.5 pl-3 text-right font-semibold">P. unit.</th>
                <th scope="col" className="py-1.5 pr-3 pl-3 text-right font-semibold">Importe</th>
              </tr>
            </thead>
            <tbody>
              {quote.lines.map((line, i) => (
                <tr key={`${line.sku}-${i}`} className="border-rule border-b">
                  <td className="font-figures py-2 pl-3 font-medium">{line.sku}</td>
                  <td className="py-2 pl-3">{line.product_name}</td>
                  <td className="font-figures py-2 pl-3 text-right">{line.quantity}</td>
                  <td className="font-figures py-2 pl-3 text-right">{formatAmount(line.unit_price)}</td>
                  <td className="font-figures py-2 pr-3 pl-3 text-right">{formatAmount(line.line_subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="relative flex flex-col-reverse gap-4 p-3 sm:flex-row sm:items-end sm:justify-between">
          <p className="text-ink-faint max-w-xs text-xs">
            Montos en {quote.currency}, calculados con redondeo al céntimo sobre precios y política del catálogo.
          </p>
          <dl className="font-figures grid w-full max-w-[18rem] grid-cols-[1fr_auto] gap-x-6 gap-y-1 self-end text-sm">
            <dt className="text-ink-soft font-sans">Subtotal</dt>
            <dd className="text-right">{formatAmount(quote.subtotal)}</dd>
            <dt className="text-ink-soft font-sans">Descuento {formatPercent(quote.discount_pct)}</dt>
            <dd className="text-right">
              {Number(quote.discount_amount) === 0 ? formatAmount('0') : `−${formatAmount(quote.discount_amount)}`}
            </dd>
            <dt className="border-rule-strong border-t pt-1 font-sans font-semibold">Neto</dt>
            <dd className="border-rule-strong border-t pt-1 text-right font-semibold">{formatAmount(quote.net)}</dd>
            <dt className="text-ink-soft font-sans">IGV</dt>
            <dd className="text-right">{formatAmount(quote.tax_amount)}</dd>
            <dt className="border-ink mt-1 border-t-2 pt-1.5 font-sans text-base font-bold">Total</dt>
            <dd className="border-ink mt-1 border-t-2 pt-1.5 text-right text-lg font-bold">
              {formatMoney(quote.total, quote.currency)}
            </dd>
          </dl>
          {decision && (
            <Stamp
              decision={decision}
              fresh={freshStamp}
              className="absolute top-5 right-[21rem] hidden sm:inline-flex"
            />
          )}
        </div>
      </div>
    </section>
  )
}
