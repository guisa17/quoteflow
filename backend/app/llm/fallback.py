"""Respaldo explicito del extractor real (RF-10).

Si el proveedor no responde (`ProviderUnavailable`: sin key, cuota agotada,
5xx, red), la solicitud se lee con el extractor de reglas y la procedencia lo
dice: `source = "reglas locales (respaldo: <motivo>)"`. El nodo `extract`
copia `source` al registro de auditoria, asi que el respaldo nunca es
silencioso.

Una salida fuera de esquema (`ExtractionError` a secas) no activa el
respaldo: sube al grafo para que RF-05 reintente y, si persiste, degrade a
`NEEDS_CLARIFICATION` / `EXTRACTION_FAILED`.
"""

from app.domain.models import Extraction
from app.llm.base import Extractor
from app.llm.gemini_extractor import ProviderUnavailable

RULES_SOURCE = "reglas locales"


class FallbackExtractor:
    def __init__(self, primary: Extractor, fallback: Extractor) -> None:
        self._primary = primary
        self._fallback = fallback

    async def extract(self, raw_text: str) -> Extraction:
        try:
            return await self._primary.extract(raw_text)
        except ProviderUnavailable as exc:
            extraction = await self._fallback.extract(raw_text)
            return extraction.model_copy(update={"source": f"{RULES_SOURCE} (respaldo: {exc})"})
