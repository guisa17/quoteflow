"""T4 -- motor de precios. AC-01 debe reproducirse al centavo (RF-06)."""

from decimal import Decimal

from app.domain.models import ResolvedLine
from app.domain.pricing import calculate_quote


def test_ac01_standard_case_matches_reference_example_exactly() -> None:
    """20 x HX-200 a 45.00, GOLD, 8% de descuento -- el caso de referencia."""
    lines = [
        ResolvedLine(
            sku="HX-200",
            product_name="Casco HX-200",
            quantity=20,
            unit_price=Decimal("45.00"),
            available=350,
        )
    ]
    quote = calculate_quote(lines, discount_pct=Decimal("8"), tax_rate=Decimal("0.18"))

    assert quote.subtotal == Decimal("900.00")
    assert quote.discount_amount == Decimal("72.00")
    assert quote.net == Decimal("828.00")
    assert quote.tax_amount == Decimal("149.04")
    assert quote.total == Decimal("977.04")


def test_s3_threshold_case_no_discount() -> None:
    """60 x AR-450 -- neto supera USD 10 000 (AC-03)."""
    lines = [
        ResolvedLine(
            sku="AR-450",
            product_name="Arnes de cuerpo entero",
            quantity=60,
            unit_price=Decimal("215.00"),
            available=80,
        )
    ]
    quote = calculate_quote(lines, discount_pct=Decimal("0"), tax_rate=Decimal("0.18"))

    assert quote.subtotal == Decimal("12900.00")
    assert quote.net == Decimal("12900.00")
    assert quote.tax_amount == Decimal("2322.00")
    assert quote.total == Decimal("15222.00")


def test_s4_discount_exception_case() -> None:
    """40 x BT-900, 10% solicitado (excede el 5% de STANDARD) -- AC-04."""
    lines = [
        ResolvedLine(
            sku="BT-900",
            product_name="Botas dielectricas",
            quantity=40,
            unit_price=Decimal("89.00"),
            available=140,
        )
    ]
    quote = calculate_quote(lines, discount_pct=Decimal("10"), tax_rate=Decimal("0.18"))

    assert quote.subtotal == Decimal("3560.00")
    assert quote.discount_amount == Decimal("356.00")
    assert quote.net == Decimal("3204.00")
    assert quote.total == Decimal("3780.72")


def test_multi_line_quote_sums_rounded_line_subtotals() -> None:
    lines = [
        ResolvedLine(
            sku="HX-200",
            product_name="Casco",
            quantity=3,
            unit_price=Decimal("45.00"),
            available=350,
        ),
        ResolvedLine(
            sku="GL-500",
            product_name="Guantes",
            quantity=5,
            unit_price=Decimal("18.50"),
            available=1200,
        ),
    ]
    quote = calculate_quote(lines, discount_pct=Decimal("0"), tax_rate=Decimal("0.18"))
    # 3 x 45.00 = 135.00 ; 5 x 18.50 = 92.50 => 227.50
    assert quote.subtotal == Decimal("227.50")


def test_zero_discount_produces_zero_discount_amount() -> None:
    lines = [
        ResolvedLine(
            sku="LN-120",
            product_name="Lentes",
            quantity=1,
            unit_price=Decimal("12.75"),
            available=2000,
        )
    ]
    quote = calculate_quote(lines, discount_pct=Decimal("0"), tax_rate=Decimal("0.18"))
    assert quote.discount_amount == Decimal("0.00")


def test_rounding_uses_half_up_not_bankers_rounding_on_a_boundary_value() -> None:
    """Guarda contra una regresion silenciosa al default ROUND_HALF_EVEN de Decimal."""
    lines = [
        ResolvedLine(
            sku="X", product_name="X", quantity=1, unit_price=Decimal("1.005"), available=10
        )
    ]
    quote = calculate_quote(lines, discount_pct=Decimal("0"), tax_rate=Decimal("0"))
    assert quote.subtotal == Decimal("1.01")
