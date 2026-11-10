/**
 * Puerto de `backend/app/domain/manipulation.py` (BR-18) para el modo mock.
 * Mismos patrones sobre texto normalizado (minúsculas, sin tildes): un pedido
 * que intenta dar órdenes al sistema va a revisión humana, nunca sale como
 * borrador en silencio. Pedir descuento o decir "somos clientes Gold" no
 * coincide.
 */

const PATTERNS: [label: string, pattern: RegExp][] = [
  ['ignorar instrucciones o politicas', /\bignor\w*\b.{0,40}\b(politic|instruc|regla|indicac)\w*/],
  ['ignore instructions', /\bignore\b.{0,30}\b(previous|prior|above|all)\b/],
  ['nota o mensaje del sistema', /\b(nota|mensaje|instruccion|aviso)\w* (del|para el) (sistema|asistente|modelo)\b/],
  ['se dirige al asistente o modelo', /\b(asistente|system prompt|prompt del sistema|modelo de lenguaje|ia)\s*[:,]/],
  ['asigna un rol al sistema', /\beres un (sistema|asistente|agente|modelo)\b/],
  ['reclama autoridad', /\bautoridad (total|absoluta|plena)\b/],
  ['ordena aprobar', /\baprueb\w* (automatica\w*|sin (revision|aprobacion|consultar))/],
  ['ordena marcar como aprobada', /\bmarca\w*\b.{0,40}\bcomo (aprobad|autorizad)\w*/],
  ['fija precio o nivel', /\b(fija|cambia|establece|asigna|modifica)\w*\b.{0,25}\b(precio|nivel|tier)\b/],
  ['pide ocultar', /\bno (menciones|digas|reveles|muestres)\b/],
  ['etiquetas de sistema', /<\/?\s*(system|sistema|instrucciones)\s*>|\[\s*(system|sistema)\b/],
]

function normalize(text: string): string {
  return text.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '')
}

export function detectManipulation(rawText: string): string[] {
  const normalized = normalize(rawText)
  return PATTERNS.filter(([, pattern]) => pattern.test(normalized)).map(([label]) => label)
}
