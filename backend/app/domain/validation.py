"""Validacion de completitud e integridad (BR-10..BR-13).

Funciones puras sin conocimiento del grafo -- los nodos del grafo (T9) las
invocan y traducen su resultado a routing (T10). Dos pasos separados porque
ocurren en momentos distintos del flujo: la completitud se verifica sobre la
extraccion cruda, antes de tocar catalogo o inventario (BR-10/11); la
resolucion de SKU y stock ocurre despues, ya contra el dominio (BR-12/13).
"""

from collections import Counter

from pydantic import BaseModel

from app.domain.enums import ReasonCode
from app.domain.models import ApprovalReason, ExtractedLineItem, Extraction, ResolvedLine
from app.domain.repositories import CatalogRepository, InventoryRepository


class ValidationResult(BaseModel):
    ok: bool
    blocking_reason: ApprovalReason | None = None


def check_completeness(extraction: Extraction) -> ValidationResult:
    """BR-10: al menos un item con referencia de producto y cantidad entera > 0.
    BR-11: sede, fecha requerida y descuento son opcionales -- su ausencia
    no bloquea (el descuento ausente se trata como 0% en pricing.py)."""
    if not extraction.items:
        return ValidationResult(
            ok=False,
            blocking_reason=ApprovalReason(
                reason_code=ReasonCode.MISSING_PRODUCT_REFERENCE,
                detail="No se identificó ningún producto en la solicitud.",
            ),
        )

    for item in extraction.items:
        if not item.product_reference or not item.product_reference.strip():
            return ValidationResult(
                ok=False,
                blocking_reason=ApprovalReason(
                    reason_code=ReasonCode.MISSING_PRODUCT_REFERENCE,
                    detail="Uno de los items no tiene una referencia de producto.",
                ),
            )
        if item.quantity is None or item.quantity <= 0:
            return ValidationResult(
                ok=False,
                blocking_reason=ApprovalReason(
                    reason_code=ReasonCode.MISSING_QUANTITY,
                    detail=f"Falta una cantidad válida para '{item.product_reference}'.",
                ),
            )

    return ValidationResult(ok=True)


def resolve_and_check_stock(
    items: list[ExtractedLineItem],
    catalog: CatalogRepository,
    inventory: InventoryRepository,
) -> tuple[list[ResolvedLine], ApprovalReason | None]:
    """BR-12/BR-13. Se asume que `check_completeness` ya paso (todo item tiene
    referencia y cantidad > 0). Primer fallo detiene todo -- BR-12: "no se
    cotizan parcialmente los items restantes". BR-13 compara lo disponible con
    la cantidad acumulada por SKU, no con cada linea por separado."""
    resolved: list[ResolvedLine] = []
    requested: Counter[str] = Counter()

    for item in items:
        product = catalog.get(item.product_reference)
        if product is None:
            return [], ApprovalReason(
                reason_code=ReasonCode.UNKNOWN_SKU,
                detail=f"'{item.product_reference}' no existe en el catálogo o está inactivo.",
            )

        available = inventory.available(product.sku)
        quantity = item.quantity or 0
        requested[product.sku] += quantity
        if available is None or requested[product.sku] > available:
            return [], ApprovalReason(
                reason_code=ReasonCode.INSUFFICIENT_STOCK,
                detail=(
                    f"Disponible de {product.sku}: {available or 0}. "
                    f"Solicitado: {requested[product.sku]}."
                ),
            )

        resolved.append(
            ResolvedLine(
                sku=product.sku,
                product_name=product.name,
                quantity=quantity,
                unit_price=product.list_price_usd,
                available=available,
            )
        )

    return resolved, None
