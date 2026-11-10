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

from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from app.domain.models import Extraction
from app.llm.base import Extractor, ProviderUnavailable

RULES_SOURCE = "reglas locales"


@traceable(
    run_type="chain",
    name="rules.extract",
    process_inputs=lambda inputs: {"raw_text": inputs.get("raw_text")},
)
async def _read_with_rules(extractor: Extractor, raw_text: str) -> Extraction:
    """Paso propio en la traza: el arbol muestra `gemini.extract` con error y,
    a continuacion, quien leyo el texto en su lugar."""
    return await extractor.extract(raw_text)


class FallbackExtractor:
    def __init__(self, primary: Extractor, fallback: Extractor) -> None:
        self._primary = primary
        self._fallback = fallback

    @traceable(
        run_type="chain",
        name="extractor",
        process_inputs=lambda inputs: {"raw_text": inputs.get("raw_text")},
    )
    async def extract(self, raw_text: str) -> Extraction:
        try:
            return await self._primary.extract(raw_text)
        except ProviderUnavailable as exc:
            # En LangSmith: etiqueta filtrable y motivo, para contar cuantas
            # solicitudes se leyeron con reglas y por que.
            run = get_current_run_tree()
            if run is not None:
                run.add_tags(["respaldo"])
                run.add_metadata({"fallback_reason": str(exc)})
            extraction = await _read_with_rules(self._fallback, raw_text)
            return extraction.model_copy(update={"source": f"{RULES_SOURCE} (respaldo: {exc})"})
