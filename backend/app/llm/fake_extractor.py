"""Extractor determinista para pruebas (RF-10, T8).

No llama a ningun LLM: interpreta `raw_text` con reglas de texto puras sobre
la forma tipica de una solicitud de cotizacion (una referencia con forma
XX-000, un numero cercano como cantidad, un "%" como descuento solicitado).

Deliberadamente no lee `app/domain/repositories.py` ni ningun archivo de
`app/data/` -- ADR-002 regla 1: el LLM (real o fake) "no accede a inventario
ni a politica; solo lee el texto del cliente". Que "ZZ-999" no exista en el
catalogo es un problema que decide `resolve_catalog` (dominio, T9), no este
modulo: por eso el patron de SKU es puramente estructural (dos letras, guion,
tres digitos), no una lista de SKU validos.

Resuelve los 8 escenarios de `sample_requests.json` (ver
`tests/unit/test_extraction_sanitization.py`) y cualquier texto con la misma
forma general. No es un sustituto de un LLM real: es deliberadamente rigido,
como cualquier test double -- la variedad real del lenguaje comercial es
justo el problema que resuelve el extractor real (`gemini_extractor.py`).
Tambien es el respaldo cuando el proveedor no responde (`fallback.py`).
"""

import re
from decimal import Decimal

from app.domain.models import ExtractedLineItem, Extraction
from app.llm.base import ExtractionError

_SKU_RE = re.compile(r"\b[A-Za-z]{2}-\d{3}\b")
# Un numero seguido de "%" (entero o con decimales, con punto o coma) es un
# descuento, no una cantidad. La coma decimal es la habitual en espanol:
# "7,5 %" leido como "5 %" seria un descuento equivocado sin aviso.
_NUMBER_RE = re.compile(r"\b\d+\b(?![\d.,]*\s*%)")
_DISCOUNT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_SITE_RE = re.compile(
    r"\bpara\s+(?:la\s+|el\s+)?(?:planta|obra|proyecto)?\s*(?:de\s+)?"
    r"([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*)*)"
)

_QUANTITY_WINDOW_CHARS = 45


def _quantity_before(text: str, sku_start: int, previous_sku_end: int) -> int | None:
    """La cantidad es el numero mas cercano que precede al SKU, dentro de una
    ventana corta de caracteres. La ventana va desde el SKU anterior hasta
    justo antes de este, asi que nunca incluye los digitos de un SKU (ej. el
    "200" de HX-200): tomarlos seria inventar una cantidad (BR-01)."""
    window_start = max(previous_sku_end, sku_start - _QUANTITY_WINDOW_CHARS)
    window = text[window_start:sku_start]
    numbers = list(_NUMBER_RE.finditer(window))
    if not numbers:
        return None
    return int(numbers[-1].group())


def _extract_site(text: str) -> str | None:
    match = _SITE_RE.search(text)
    if match is None:
        return None
    return match.group(1).rstrip(".,")


def _extract_discount(text: str) -> Decimal | None:
    """Extrae el primer "N%" del texto tal cual aparece -- incluido un intento
    de inyeccion de prompt (S8): el texto se interpreta, no se juzga aqui.
    Que 40% supere el techo duro lo decide policy.py (dominio), no esto."""
    match = _DISCOUNT_RE.search(text)
    if match is None:
        return None
    return Decimal(match.group(1).replace(",", "."))


class FakeExtractor:
    """Implementa el `Extractor` Protocol (`app/llm/base.py`) sin red.

    `force_failure=True` simula el caso que RF-05 llama "fallo recuperable":
    un extractor real que no logra producir una salida valida (JSON
    malformado, proveedor caido, timeout). Es la unica forma soportada de
    disparar `ExtractionError` desde este extractor -- deliberadamente no
    existe un texto "magico" que la dispare, para no acoplar el
    comportamiento de fallo al contenido de un texto arbitrario del cliente.
    """

    def __init__(self, force_failure: bool = False) -> None:
        self._force_failure = force_failure

    async def extract(self, raw_text: str) -> Extraction:
        if self._force_failure:
            raise ExtractionError("Fallo simulado del extractor (force_failure=True).")

        items: list[ExtractedLineItem] = []
        previous_sku_end = 0
        for match in _SKU_RE.finditer(raw_text):
            items.append(
                ExtractedLineItem(
                    product_reference=match.group(),
                    quantity=_quantity_before(raw_text, match.start(), previous_sku_end),
                )
            )
            previous_sku_end = match.end()

        return Extraction(
            items=items,
            site=_extract_site(raw_text),
            requested_discount_pct=_extract_discount(raw_text),
        )
