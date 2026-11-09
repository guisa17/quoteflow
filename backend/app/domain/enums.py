from enum import StrEnum


class Outcome(StrEnum):
    """Los cinco resultados terminales de una solicitud."""

    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    DRAFT_READY = "DRAFT_READY"
    BLOCKED = "BLOCKED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"


class ReasonCode(StrEnum):
    """Motivo especifico detras de un Outcome. Citado por BR-xx en REQUIREMENTS.md."""

    MISSING_PRODUCT_REFERENCE = "MISSING_PRODUCT_REFERENCE"  # BR-10
    MISSING_QUANTITY = "MISSING_QUANTITY"  # BR-10
    UNKNOWN_SKU = "UNKNOWN_SKU"  # BR-02, BR-12
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"  # BR-13
    THRESHOLD_EXCEEDED = "THRESHOLD_EXCEEDED"  # BR-05
    DISCOUNT_EXCEPTION = "DISCOUNT_EXCEPTION"  # BR-06
    UNKNOWN_CUSTOMER = "UNKNOWN_CUSTOMER"  # BR-08
    DISCOUNT_ABOVE_HARD_CEILING = "DISCOUNT_ABOVE_HARD_CEILING"  # BR-07
    EXTRACTION_FAILED = "EXTRACTION_FAILED"  # RF-05, fallo recuperable


class Tier(StrEnum):
    """Nivel comercial del cliente. Determina el descuento maximo autorizado."""

    GOLD = "GOLD"
    SILVER = "SILVER"
    STANDARD = "STANDARD"


class DecisionAction(StrEnum):
    """BR-14: las tres acciones posibles de una decision humana."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OBSERVE = "OBSERVE"
