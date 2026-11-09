import { Copy } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

/** RF-09.5 — ver el borrador final cuando `outcome = DRAFT_READY`. Texto
 * plano generado por plantilla determinista (ADR-002 regla 5: la redacción
 * no introduce cifras que el dominio no haya calculado ya). */
export function DraftCard({ draftText }: { draftText: string }) {
  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(draftText)
      toast.success('Borrador copiado al portapapeles.')
    } catch {
      toast.error('No se pudo copiar. Selecciona el texto manualmente.')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Borrador</CardTitle>
        <CardDescription>Listo para revisión — el MVP prepara borradores, no envía nada al cliente.</CardDescription>
      </CardHeader>
      <CardContent>
        <pre className="bg-muted/60 font-figures max-h-96 overflow-auto rounded-md p-4 text-xs whitespace-pre-wrap">
          {draftText}
        </pre>
      </CardContent>
      <CardFooter>
        <Button variant="outline" size="sm" onClick={handleCopy}>
          <Copy aria-hidden />
          Copiar
        </Button>
      </CardFooter>
    </Card>
  )
}
