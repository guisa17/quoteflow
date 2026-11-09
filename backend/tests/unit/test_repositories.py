"""T3 -- repositorios sobre el seed real de app/data/*.json."""

from decimal import Decimal

from app.domain.enums import Tier
from app.domain.repositories import (
    CatalogRepository,
    CustomerRepository,
    InventoryRepository,
    PolicyRepository,
)


def test_customer_repository_finds_known_customer_with_correct_tier() -> None:
    repo = CustomerRepository()
    customer = repo.get("FER-1001")
    assert customer is not None
    assert customer.tier is Tier.GOLD


def test_customer_repository_returns_none_for_unknown_customer() -> None:
    repo = CustomerRepository()
    assert repo.get("FER-9999") is None


def test_catalog_repository_finds_the_reference_sku() -> None:
    repo = CatalogRepository()
    product = repo.get("HX-200")
    assert product is not None
    assert product.list_price_usd == Decimal("45.00")
    assert isinstance(product.list_price_usd, Decimal)


def test_catalog_repository_returns_none_for_unknown_sku_no_fuzzy_match() -> None:
    """BR-02: sin sustitucion por similitud. ZZ-999 nunca resuelve a nada."""
    repo = CatalogRepository()
    assert repo.get("ZZ-999") is None


def test_catalog_repository_normalizes_case_whitespace_and_repeated_hyphens() -> None:
    repo = CatalogRepository()
    canonical = repo.get("HX-200")
    assert canonical is not None
    for variant in ("hx-200", " HX-200 ", "HX--200", "HX  -  200".replace("  ", " ")):
        resolved = repo.get(variant)
        assert resolved is not None
        assert resolved.sku == canonical.sku


def test_inventory_repository_computes_available_for_seed_scenarios() -> None:
    repo = InventoryRepository()
    # S5: RP-300, on_hand=95 reserved=15 -> disponible 80 < 300 solicitados
    assert repo.available("RP-300") == 80
    # S3: AR-450, on_hand=90 reserved=10 -> disponible 80 >= 60 solicitados
    assert repo.available("AR-450") == 80


def test_inventory_repository_returns_none_for_unknown_sku() -> None:
    repo = InventoryRepository()
    assert repo.available("ZZ-999") is None


def test_policy_repository_loads_thresholds_from_seed() -> None:
    policy = PolicyRepository().get()
    assert policy.approval_threshold_usd == Decimal("10000.00")
    assert policy.hard_discount_ceiling_pct == Decimal("20.0")
    assert policy.max_discount_pct_for(Tier.GOLD) == Decimal("12.0")
    assert policy.max_discount_pct_for(Tier.SILVER) == Decimal("8.0")
    assert policy.max_discount_pct_for(Tier.STANDARD) == Decimal("5.0")
    assert policy.tax.rate == Decimal("0.18")
