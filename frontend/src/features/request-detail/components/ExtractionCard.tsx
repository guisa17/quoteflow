import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { formatPercent } from '@/lib/money'
import type { Extraction } from '@/types/api'

/** RF-09.3 — "extracción": lo que el sistema entendió del texto libre,
 * antes de tocar catálogo o inventario. Mostrar esto por separado de la
 * cotización es lo que hace visible BR-01/BR-03: el LLM solo interpretó
 * intención, nunca inventó precio ni stock. */
export function ExtractionCard({ extraction }: { extraction: Extraction | null }) {
  if (!extraction) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Extracción</CardTitle>
          <CardDescription>La extracción falló (EXTRACTION_FAILED) y no produjo salida.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Extracción</CardTitle>
        <CardDescription>Salida estructurada del texto libre, antes de resolver dominio.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {extraction.items.length > 0 ? (
          <ul className="divide-border divide-y">
            {extraction.items.map((item, i) => (
              <li key={i} className="flex items-center justify-between py-1.5 text-sm">
                <span className="font-figures">{item.product_reference}</span>
                <span className="text-muted-foreground font-figures">
                  {item.quantity !== null ? `cantidad: ${item.quantity}` : 'cantidad: —'}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-muted-foreground text-sm">Ningún ítem identificado en el texto.</p>
        )}

        <dl className="grid grid-cols-3 gap-3 border-t pt-3 text-xs">
          <div>
            <dt className="text-muted-foreground">Sede</dt>
            <dd className="mt-0.5 font-medium">{extraction.site ?? 'a confirmar'}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Fecha requerida</dt>
            <dd className="mt-0.5 font-medium">{extraction.requested_date ?? 'a confirmar'}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Descuento solicitado</dt>
            <dd className="font-figures mt-0.5 font-medium">
              {extraction.requested_discount_pct
                ? formatPercent(extraction.requested_discount_pct)
                : '0% (no solicitado)'}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  )
}
