"""Frontera del LLM (ADR-002, T8).

Protocolo minimo que cualquier extractor -- real o de pruebas -- debe cumplir.
El extractor real (`app/llm/anthropic_extractor.py`) esta fuera del alcance de
T7-T11: se construye en el ciclo acotado de `LOOP.md`, sobre este mismo
Protocol. Aqui solo vive el contrato y el tipo de error que ambos comparten.

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


@runtime_checkable
class Extractor(Protocol):
    """Contrato compartido por el extractor fake (T8) y el real (LOOP.md)."""

    async def extract(self, raw_text: str) -> Extraction:
        """Interpreta `raw_text` y devuelve una `Extraction` validada.

        Lanza `ExtractionError` si no puede -- nunca devuelve una extraccion
        a medias ni inventa un valor para completarla.
        """
        ...
