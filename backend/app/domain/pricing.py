"""Motor de precios determinista (RF-06, BR-04).

No decide nada: recibe lineas ya resueltas contra catalogo/inventario y un
porcentaje de descuento ya validado por policy.py, y calcula. Si algun dia
este modulo empieza a preguntarse "es valido este descuento?", esa logica se
escapo de policy.py y hay que devolverla a su lugar.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.domain.models import Quote, ResolvedLine

CENTS = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    """BR-04: ROUND_HALF_UP explicito -- el default de Decimal es ROUND_HALF_EVEN."""
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def calculate_quote(
    lines: list[ResolvedLine],
    discount_pct: Decimal,
    tax_rate: Decimal,
    currency: str = "USD",
) -> Quote:
    """RF-06: subtotal por linea -> subtotal total -> descuento -> neto -> IGV -> total.

    El redondeo ocurre a nivel de linea (evita arrastre de centavos en
    cotizaciones multi-linea) y en cada paso monetario subsecuente.
    """
    line_subtotals = [_round(line.unit_price * line.quantity) for line in lines]
    subtotal = sum(line_subtotals, start=Decimal("0.00"))

    discount_amount = _round(subtotal * discount_pct / Decimal(100))
    net = subtotal - discount_amount
    tax_amount = _round(net * tax_rate)
    total = net + tax_amount

    return Quote(
        lines=lines,
        subtotal=subtotal,
        discount_pct=discount_pct,
        discount_amount=discount_amount,
        net=net,
        tax_amount=tax_amount,
        total=total,
        currency=currency,
    )
