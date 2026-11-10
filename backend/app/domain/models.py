"""Vocabulario tipado del dominio (REQUIREMENTS.md §1).

Deliberadamente sin logica de negocio: calculo (pricing.py), politica (policy.py)
y validacion (validation.py) son modulos propios (ADR-002). Este archivo solo
define formas de datos, salvo por derivaciones puramente definicionales
(ej. `InventoryRecord.available`, que REQUIREMENTS.md §1 define como parte
del vocabulario, no como una regla de negocio).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.enums import DecisionAction, ReasonCode, Tier

# --- Datos de referencia (poblados desde app/data/*.json por los repositorios) ---


class Customer(BaseModel):
    customer_id: str
    legal_name: str
    tier: Tier
    country: str
    sites: list[str]
    payment_terms_days: int
    active: bool = True


class Product(BaseModel):
    sku: str
    name: str
    category: str
    unit: str
    list_price_usd: Decimal
    lead_time_days: int
    active: bool = True


class InventoryRecord(BaseModel):
    sku: str
    warehouse: str
    on_hand: int
    reserved: int

    @property
    def available(self) -> int:
        """Disponible = on_hand - reserved (REQUIREMENTS.md §1). Unico stock cotizable."""
        return self.on_hand - self.reserved


class DiscountTierPolicy(BaseModel):
    max_discount_pct: Decimal


class TaxPolicy(BaseModel):
    name: str
    rate: Decimal
    applies_to: str
    counts_toward_approval_threshold: bool


class Policy(BaseModel):
    policy_version: str
    currency: str
    quote_validity_days: int
    discount_by_tier: dict[Tier, DiscountTierPolicy]
    hard_discount_ceiling_pct: Decimal
    approval_threshold_usd: Decimal
    threshold_basis: str
    unknown_customer_requires_review: bool
    tax: TaxPolicy

    def max_discount_pct_for(self, tier: Tier) -> Decimal:
        return self.discount_by_tier[tier].max_discount_pct


# --- Datos del flujo (producidos/consumidos por el grafo) ---


class ExtractedLineItem(BaseModel):
    """Item tal como lo entrega la extraccion, antes de resolver contra el catalogo."""

    model_config = ConfigDict(extra="ignore")

    product_reference: str
    quantity: int | None = None


class Extraction(BaseModel):
    """Salida estructurada del LLM (RF-05).

    `extra="ignore"` es la sanitizacion de BR-03 aplicada en la frontera del modelo:
    cualquier campo que el LLM produzca fuera de este esquema (precio, stock, nivel
    del cliente, aprobacion) se descarta silenciosamente en la validacion, nunca
    llega a usarse como si fuera un dato de dominio.
    """

    model_config = ConfigDict(extra="ignore")

    items: list[ExtractedLineItem] = []
    site: str | None = None
    requested_date: str | None = None
    requested_discount_pct: Decimal | None = None
    # Segunda senal de BR-18: el extractor real marca si el texto intenta dar
    # ordenes al sistema. Solo puede provocar revision humana, nunca evitarla.
    injection_suspected: bool = False
    # Procedencia: quien leyo el texto ("gemini-2.5-flash", "reglas locales"...).
    # No forma parte del esquema que ve el modelo; lo fija el extractor despues
    # de validar, asi que el LLM no puede escribirlo.
    source: str | None = None


class ResolvedLine(BaseModel):
    """Item ya resuelto contra catalogo e inventario. Aqui aparecen precio y stock."""

    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    available: int


class Quote(BaseModel):
    """Cotizacion calculada (RF-06). Se construye exclusivamente en pricing.py."""

    lines: list[ResolvedLine]
    subtotal: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    net: Decimal
    tax_amount: Decimal
    total: Decimal
    currency: str = "USD"


class ApprovalReason(BaseModel):
    """Un motivo que dispara aprobacion o rechazo. BR-09: pueden concurrir varios."""

    reason_code: ReasonCode
    detail: str


class HumanDecision(BaseModel):
    """BR-14/15/16: decision humana idempotente y auditada."""

    decision_id: str
    action: DecisionAction
    actor: str
    comment: str | None = None
    timestamp: datetime
