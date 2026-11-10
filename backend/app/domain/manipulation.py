"""Deteccion determinista de intentos de manipulacion en el texto del cliente.

BR-17 ya garantiza que el texto del cliente nunca se trata como instruccion:
el extractor no puede escribir precio, nivel ni aprobacion. Eso evita que el
ataque funcione, pero no que pase desapercibido. Un pedido que intenta dar
ordenes al sistema ("nota del sistema", "fija el precio", "no menciones esto")
no debe salir como borrador sin que una persona lo vea.

Este modulo no depende del LLM, que es justamente el componente atacado: son
patrones sobre el texto normalizado (minusculas, sin tildes). El extractor
real aporta una segunda senal (`Extraction.injection_suspected`); cualquiera
de las dos basta para pedir revision humana, y ninguna puede anular a la otra.

Los patrones apuntan a frases dirigidas al sistema, no a pedidos comerciales
legitimos: "somos clientes Gold" o "nos pueden dar 10% de descuento" no
coinciden.
"""

import re
import unicodedata

# (etiqueta legible, patron sobre texto normalizado)
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (label, re.compile(pattern))
    for label, pattern in [
        (
            "ignorar instrucciones o políticas",
            r"\bignor\w*\b.{0,40}\b(politic|instruc|regla|indicac)\w*",
        ),
        ("ignore instructions", r"\bignore\b.{0,30}\b(previous|prior|above|all)\b"),
        (
            "nota o mensaje del sistema",
            r"\b(nota|mensaje|instruccion|aviso)\w* (del|para el) (sistema|asistente|modelo)\b",
        ),
        (
            "se dirige al asistente o modelo",
            r"\b(asistente|system prompt|prompt del sistema|modelo de lenguaje|ia)\s*[:,]",
        ),
        ("asigna un rol al sistema", r"\beres un (sistema|asistente|agente|modelo)\b"),
        ("reclama autoridad", r"\bautoridad (total|absoluta|plena)\b"),
        ("ordena aprobar", r"\baprueb\w* (automatica\w*|sin (revision|aprobacion|consultar))"),
        ("ordena marcar como aprobada", r"\bmarca\w*\b.{0,40}\bcomo (aprobad|autorizad)\w*"),
        # Pedir descuento es legitimo (lo evalua la politica); fijar precio o
        # nivel del cliente no lo es.
        (
            "fija precio o nivel",
            r"\b(fija|cambia|establece|asigna|modifica)\w*\b.{0,25}\b(precio|nivel|tier)\b",
        ),
        ("pide ocultar", r"\bno (menciones|digas|reveles|muestres)\b"),
        (
            "etiquetas de sistema",
            r"</?\s*(system|sistema|instrucciones)\s*>|\[\s*(system|sistema)\b",
        ),
    ]
]


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def detect_manipulation(raw_text: str) -> list[str]:
    """Etiquetas de los patrones encontrados, en orden; vacia si no hay ninguno."""
    normalized = _normalize(raw_text)
    return [label for label, pattern in _PATTERNS if pattern.search(normalized)]
