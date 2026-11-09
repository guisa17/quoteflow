import { Check, Copy } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

/** El borrador listo para enviar por el canal del operador. Lo arma una
 * plantilla con cifras ya calculadas; QuoteFlow no envía nada al cliente. */
export function DraftCard({ draftText }: { draftText: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(draftText)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      toast.error('No se pudo copiar. Selecciona el texto y cópialo a mano.')
    }
  }

  return (
    <section aria-labelledby="draft-title">
      <div className="flex items-center justify-between">
        <h2 id="draft-title" className="field-label">
          Borrador para el cliente
        </h2>
        <button
          type="button"
          onClick={handleCopy}
          className="text-ink-soft hover:text-ink inline-flex h-7 items-center gap-1.5 rounded-md px-2 text-xs font-semibold transition-colors"
        >
          {copied ? <Check aria-hidden className="size-3.5" /> : <Copy aria-hidden className="size-3.5" />}
          {copied ? 'Copiado' : 'Copiar texto'}
        </button>
      </div>
      <pre className="bg-green/50 border-rule-strong font-figures mt-2 max-h-96 overflow-auto rounded-sm border p-4 text-sm leading-relaxed whitespace-pre-wrap">
        {draftText}
      </pre>
    </section>
  )
}
