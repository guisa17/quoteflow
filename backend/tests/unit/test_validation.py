"""T6 -- validacion de completitud (BR-10/11) e integridad de SKU/stock (BR-12/13)."""

from decimal import Decimal

from app.domain.enums import ReasonCode
from app.domain.models import ExtractedLineItem, Extraction
from app.domain.repositories import CatalogRepository, InventoryRepository
from app.domain.validation import check_completeness, resolve_and_check_stock


def test_s2_missing_quantity_blocks_before_calculating_anything() -> None:
    extraction = Extraction(items=[ExtractedLineItem(product_reference="HX-200", quantity=None)])
    result = check_completeness(extraction)
    assert not result.ok
    assert result.blocking_reason is not None
    assert result.blocking_reason.reason_code == ReasonCode.MISSING_QUANTITY


def test_no_items_at_all_is_missing_product_reference() -> None:
    extraction = Extraction(items=[])
    result = check_completeness(extraction)
    assert not result.ok
    assert result.blocking_reason is not None
    assert result.blocking_reason.reason_code == ReasonCode.MISSING_PRODUCT_REFERENCE


def test_zero_or_negative_quantity_is_treated_as_missing() -> None:
    extraction = Extraction(items=[ExtractedLineItem(product_reference="HX-200", quantity=0)])
    result = check_completeness(extraction)
    assert not result.ok
    assert result.blocking_reason is not None
    assert result.blocking_reason.reason_code == ReasonCode.MISSING_QUANTITY


def test_br11_missing_site_date_and_discount_do_not_block() -> None:
    extraction = Extraction(
        items=[ExtractedLineItem(product_reference="HX-200", quantity=20)],
        site=None,
        requested_date=None,
        requested_discount_pct=None,
    )
    result = check_completeness(extraction)
    assert result.ok
    assert result.blocking_reason is None


def test_s6_unknown_sku_blocks_with_no_fuzzy_substitution() -> None:
    catalog = CatalogRepository()
    inventory = InventoryRepository()
    items = [ExtractedLineItem(product_reference="ZZ-999", quantity=50)]

    lines, reason = resolve_and_check_stock(items, catalog, inventory)

    assert lines == []
    assert reason is not None
    assert reason.reason_code == ReasonCode.UNKNOWN_SKU


def test_s5_insufficient_stock_blocks_and_reports_real_availability() -> None:
    catalog = CatalogRepository()
    inventory = InventoryRepository()
    items = [ExtractedLineItem(product_reference="RP-300", quantity=300)]

    lines, reason = resolve_and_check_stock(items, catalog, inventory)

    assert lines == []
    assert reason is not None
    assert reason.reason_code == ReasonCode.INSUFFICIENT_STOCK
    assert "80" in reason.detail


def test_valid_item_resolves_with_price_and_availability() -> None:
    catalog = CatalogRepository()
    inventory = InventoryRepository()
    items = [ExtractedLineItem(product_reference="HX-200", quantity=20)]

    lines, reason = resolve_and_check_stock(items, catalog, inventory)

    assert reason is None
    assert len(lines) == 1
    assert lines[0].sku == "HX-200"
    assert lines[0].unit_price == Decimal("45.00")
    assert lines[0].available == 350


def test_br13_stock_is_checked_against_the_accumulated_quantity_per_sku() -> None:
    """Hay 80 RP-300: 80 + 1 en lineas separadas supera lo disponible, incluso
    si la segunda referencia llega escrita con otro formato."""
    catalog = CatalogRepository()
    inventory = InventoryRepository()
    items = [
        ExtractedLineItem(product_reference="RP-300", quantity=80),
        ExtractedLineItem(product_reference="rp-300", quantity=1),
    ]

    lines, reason = resolve_and_check_stock(items, catalog, inventory)

    assert lines == []
    assert reason is not None
    assert reason.reason_code == ReasonCode.INSUFFICIENT_STOCK
    assert "Disponible de RP-300: 80. Solicitado: 81." in reason.detail


def test_br13_repeated_sku_within_available_stock_keeps_both_lines() -> None:
    catalog = CatalogRepository()
    inventory = InventoryRepository()
    items = [
        ExtractedLineItem(product_reference="RP-300", quantity=79),
        ExtractedLineItem(product_reference="RP-300", quantity=1),
    ]

    lines, reason = resolve_and_check_stock(items, catalog, inventory)

    assert reason is None
    assert [line.quantity for line in lines] == [79, 1]


def test_br12_partial_failure_discards_already_resolved_lines() -> None:
    """Si el segundo item falla, no se devuelven lineas parciales del primero."""
    catalog = CatalogRepository()
    inventory = InventoryRepository()
    items = [
        ExtractedLineItem(product_reference="HX-200", quantity=1),
        ExtractedLineItem(product_reference="ZZ-999", quantity=1),
    ]

    lines, reason = resolve_and_check_stock(items, catalog, inventory)

    assert lines == []
    assert reason is not None
    assert reason.reason_code == ReasonCode.UNKNOWN_SKU
