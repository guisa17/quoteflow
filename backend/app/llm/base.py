"""Frontera del LLM (ADR-002, T8).

Protocolo minimo que cualquier extractor -- real o de pruebas -- debe cumplir.
Lo implementan `FakeExtractor` (reglas, sin red), `GeminiExtractor` (Gemini
por REST), `LangChainExtractor` (cualquier otro proveedor, ADR-006) y
`FallbackExtractor` (el extractor real con respaldo explicito a reglas). Aqui
solo viven el contrato y los tipos de error que comparten.

Un extractor:
- Recibe `raw_text`, el texto del cliente. Es entrada no confiable (BR-17):
  cualquier implementacion lo trata como dato a interpretar, nunca como
  instruccion.
- Devuelve una `Extraction` ya validada por Pydantic (RF-05). La sanitizacion
  de campos de dominio (BR-03/ADR-002 §2) ocurre automaticamente al validar:
  `Extraction` declara `extra="ignore"`, asi que precio, stock, nivel del
  cliente o aprobacion que el modelo intente producir se descartan en la
  frontera, antes de que exista una variable de Python que los contenga.
- Nunca decide nada ni accede a `app/domain/repositories.py` (ADR-002 regla 1:
  "no accede a inventario ni a politica; solo lee el texto del cliente").
- Puede fallar con `ExtractionError` si no logra producir una salida valida.
  Quien decide si reintenta o degrada a `NEEDS_CLARIFICATION` /
  `EXTRACTION_FAILED` es el nodo `extract` del grafo (T9/T10), no el
  extractor: este solo reporta el fallo, no lo absorbe en silencio.
"""

from typing import Protocol, runtime_checkable

from app.domain.models import Extraction


class ExtractionError(Exception):
    """El extractor no pudo producir una `Extraction` valida.

    Cubre tanto un esquema invalido (JSON que no valida contra `Extraction`)
    como un fallo del propio proveedor (red, timeout, respuesta vacia). RF-05
    trata ambos casos igual: un reintento, y si persiste, fallo recuperable.
    """


class ProviderUnavailable(ExtractionError):
    """El proveedor no respondio (sin key, cuota agotada, 5xx, red, timeout).

    No dice nada sobre el texto del cliente, asi que `FallbackExtractor` puede
    recurrir al extractor de reglas (RF-10). Lo lanzan todos los extractores
    reales, sea cual sea el proveedor."""


def describe_http_error(status: int) -> str:
    if status == 429:
        return "cuota del proveedor agotada (429)"
    if status in (401, 403):
        return f"API key rechazada ({status})"
    if status >= 500:
        return f"error del proveedor ({status})"
    return f"respuesta HTTP {status}"


def is_unavailable_status(status: int) -> bool:
    """Estados que indican un proveedor caido o inaccesible, no un problema
    de la salida: cuota, credenciales y errores del servidor."""
    return status == 429 or status in (401, 403) or status >= 500


@runtime_checkable
class Extractor(Protocol):
    """Contrato compartido por el extractor de reglas (T8) y el de Gemini."""

    async def extract(self, raw_text: str) -> Extraction:
        """Interpreta `raw_text` y devuelve una `Extraction` validada.

        Lanza `ExtractionError` si no puede -- nunca devuelve una extraccion
        a medias ni inventa un valor para completarla.
        """
        ...
