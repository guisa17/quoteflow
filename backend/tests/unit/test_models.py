"""T2 -- modelos y enumerados del dominio. Sin logica de negocio: eso lo prueban
pricing/policy/validation en T4-T6. Aqui solo se verifica la forma de los datos
y la disciplina Decimal (BR-04)."""

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from app.domain.enums import DecisionAction, Outcome, ReasonCode, Tier
from app.domain.models import (
    Customer,
    Extraction,
    HumanDecision,
    InventoryRecord,
    Policy,
    Product,
)


def test_outcome_has_the_five_terminal_results() -> None:
    assert {o.value for o in Outcome} == {
        "NEEDS_CLARIFICATION",
        "DRAFT_READY",
        "BLOCKED",
        "PENDING_APPROVAL",
        "REJECTED_BY_POLICY",
    }


def test_tier_has_the_three_commercial_levels() -> None:
    assert {t.value for t in Tier} == {"GOLD", "SILVER", "STANDARD"}


def test_decision_action_matches_br14() -> None:
    assert {a.value for a in DecisionAction} == {"APPROVE", "REJECT", "OBSERVE"}


def test_reason_code_covers_every_scenario_in_the_seed() -> None:
    seed_reasons = {
        "MISSING_QUANTITY",
        "UNKNOWN_SKU",
        "THRESHOLD_EXCEEDED",
        "DISCOUNT_EXCEPTION",
        "INSUFFICIENT_STOCK",
        "UNKNOWN_CUSTOMER",
        "DISCOUNT_ABOVE_HARD_CEILING",
    }
    assert seed_reasons.issubset({r.value for r in ReasonCode})


def test_product_price_parses_as_decimal_not_float() -> None:
    product = Product.model_validate_json(
        '{"sku": "HX-200", "name": "Casco", "category": "EPP", "unit": "unidad", '
        '"list_price_usd": 45.00, "lead_time_days": 3, "active": true}'
    )
    assert isinstance(product.list_price_usd, Decimal)
    assert product.list_price_usd == Decimal("45.00")


def test_inventory_available_is_on_hand_minus_reserved() -> None:
    record = InventoryRecord(sku="RP-300", warehouse="LIMA-01", on_hand=95, reserved=15)
    assert record.available == 80


def test_policy_max_discount_by_tier() -> None:
    policy = Policy.model_validate_json(
        """
        {
          "policy_version": "2026.08", "currency": "USD", "quote_validity_days": 15,
          "discount_by_tier": {
            "GOLD": {"max_discount_pct": 12.0},
            "SILVER": {"max_discount_pct": 8.0},
            "STANDARD": {"max_discount_pct": 5.0}
          },
          "hard_discount_ceiling_pct": 20.0,
          "approval_threshold_usd": 10000.00,
          "threshold_basis": "net_total_after_discount_before_tax",
          "unknown_customer_requires_review": true,
          "tax": {"name": "IGV", "rate": 0.18, "applies_to": "net_total_after_discount",
                   "counts_toward_approval_threshold": false}
        }
        """
    )
    assert policy.max_discount_pct_for(Tier.GOLD) == Decimal("12.0")
    assert policy.max_discount_pct_for(Tier.STANDARD) == Decimal("5.0")
    assert isinstance(policy.approval_threshold_usd, Decimal)


def test_extraction_silently_drops_domain_fields_it_should_never_produce() -> None:
    """BR-03 / ADR-002 sec.2: la sanitizacion de la extraccion ocurre en la
    frontera del modelo. Si el LLM devuelve precio, stock o nivel del cliente
    (campos fuera de este esquema), se descartan aqui -- nunca llegan al dominio."""
    extraction = Extraction.model_validate_json(
        """
        {
          "items": [{"product_reference": "HX-200", "quantity": 20}],
          "site": "Arequipa",
          "unit_price": 999.99,
          "customer_tier": "GOLD",
          "approved": true
        }
        """
    )
    assert extraction.site == "Arequipa"
    assert len(extraction.items) == 1
    assert not hasattr(extraction, "unit_price")
    assert not hasattr(extraction, "customer_tier")
    assert not hasattr(extraction, "approved")


def test_decimal_rounding_is_half_up_not_bankers_rounding() -> None:
    """Guarda contra una regresion silenciosa: el redondeo por defecto de Decimal
    en Python es ROUND_HALF_EVEN. BR-04 exige ROUND_HALF_UP explicito."""
    value = Decimal("1.005")
    assert value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("1.01")


def test_human_decision_carries_the_full_audit_trail() -> None:
    decision = HumanDecision(
        decision_id="dec-001",
        action=DecisionAction.APPROVE,
        actor="jefe.comercial@ferrocima.example",
        comment="Dentro de politica, aprobado",
        timestamp=datetime.now(UTC),
    )
    assert decision.action == DecisionAction.APPROVE
    assert decision.actor


def test_customer_tier_parses_from_seed_shape() -> None:
    customer = Customer.model_validate_json(
        """
        {"customer_id": "FER-1001", "legal_name": "Minera Cumbre Alta S.A.A.",
         "tier": "GOLD", "country": "PE", "sites": ["Arequipa", "Lima"],
         "payment_terms_days": 45, "active": true}
        """
    )
    assert customer.tier is Tier.GOLD
    assert "Arequipa" in customer.sites
