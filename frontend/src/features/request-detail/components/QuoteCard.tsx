import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatAmount, formatMoney, formatPercent } from '@/lib/money'
import type { Quote } from '@/types/api'

/** RF-09.3 — "cotización": el cálculo determinista (RF-06). Todos los
 * montos llegan como string decimal (docs/API_CONTRACT.md) y aquí solo se
 * formatean para mostrar -- ninguna suma ocurre en este componente. */
export function QuoteCard({ quote }: { quote: Quote }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cotización</CardTitle>
        <CardDescription>Cálculo determinista (RF-06) sobre las líneas resueltas contra catálogo e inventario.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-muted-foreground border-border border-b text-xs">
                <th className="py-1.5 pr-2 font-medium">SKU</th>
                <th className="py-1.5 pr-2 font-medium">Producto</th>
                <th className="py-1.5 pr-2 text-right font-medium">Cant.</th>
                <th className="py-1.5 pr-2 text-right font-medium">P. unitario</th>
                <th className="py-1.5 text-right font-medium">Subtotal línea</th>
              </tr>
            </thead>
            <tbody>
              {quote.lines.map((line) => (
                <tr key={line.sku} className="border-border border-b last:border-0">
                  <td className="font-figures py-2 pr-2">{line.sku}</td>
                  <td className="py-2 pr-2">{line.product_name}</td>
                  <td className="font-figures py-2 pr-2 text-right">{line.quantity}</td>
                  <td className="font-figures py-2 pr-2 text-right">{formatAmount(line.unit_price)}</td>
                  <td className="font-figures py-2 text-right">{formatAmount(line.line_subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <dl className="ml-auto grid max-w-xs grid-cols-2 gap-y-1.5 text-sm">
          <dt className="text-muted-foreground">Subtotal</dt>
          <dd className="font-figures text-right">{formatAmount(quote.subtotal)}</dd>

          <dt className="text-muted-foreground">Descuento ({formatPercent(quote.discount_pct)})</dt>
          <dd className="font-figures text-right">−{formatAmount(quote.discount_amount)}</dd>

          <dt className="text-muted-foreground border-border border-t pt-1.5 font-medium">Neto</dt>
          <dd className="font-figures border-border border-t pt-1.5 text-right font-medium">
            {formatAmount(quote.net)}
          </dd>

          <dt className="text-muted-foreground">IGV</dt>
          <dd className="font-figures text-right">{formatAmount(quote.tax_amount)}</dd>

          <dt className="border-border border-t pt-1.5 font-semibold">Total</dt>
          <dd className="font-figures border-border border-t pt-1.5 text-right text-base font-semibold">
            {formatMoney(quote.total, quote.currency)}
          </dd>
        </dl>
      </CardContent>
    </Card>
  )
}
