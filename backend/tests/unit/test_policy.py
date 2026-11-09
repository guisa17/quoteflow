"""T5 -- motor de politica. BR-05..BR-09, con enfasis en la precedencia (BR-09)."""

from decimal import Decimal

import pytest

from app.domain.enums import ReasonCode, Tier
from app.domain.policy import evaluate_policy
from app.domain.repositories import PolicyRepository


@pytest.fixture
def policy():
    return PolicyRepository().get()


def test_s1_within_policy_requires_no_approval(policy) -> None:
    result = evaluate_policy(
        tier=Tier.GOLD,
        customer_is_known=True,
        requested_discount_pct=Decimal("8"),
        net=Decimal("828.00"),
        policy=policy,
    )
    assert not result.is_rejected
    assert not result.requires_approval
    assert result.approval_reasons == []


def test_s3_threshold_exceeded_requires_approval(policy) -> None:
    result = evaluate_policy(
        tier=Tier.GOLD,
        customer_is_known=True,
        requested_discount_pct=Decimal("0"),
        net=Decimal("12900.00"),
        policy=policy,
    )
    assert not result.is_rejected
    assert result.requires_approval
    assert [r.reason_code for r in result.approval_reasons] == [ReasonCode.THRESHOLD_EXCEEDED]


def test_s4_discount_exception_requires_approval(policy) -> None:
    result = evaluate_policy(
        tier=Tier.STANDARD,
        customer_is_known=True,
        requested_discount_pct=Decimal("10"),
        net=Decimal("3204.00"),
        policy=policy,
    )
    assert not result.is_rejected
    assert [r.reason_code for r in result.approval_reasons] == [ReasonCode.DISCOUNT_EXCEPTION]


def test_s7_unknown_customer_requires_approval(policy) -> None:
    result = evaluate_policy(
        tier=Tier.STANDARD,
        customer_is_known=False,
        requested_discount_pct=Decimal("0"),
        net=Decimal("1275.00"),
        policy=policy,
    )
    assert not result.is_rejected
    assert [r.reason_code for r in result.approval_reasons] == [ReasonCode.UNKNOWN_CUSTOMER]


def test_s8_discount_above_hard_ceiling_is_rejected_not_pending(policy) -> None:
    """La inyeccion de prompt (S8) pide 40%: > techo duro 20% -> rechazo, nunca aprobacion."""
    result = evaluate_policy(
        tier=Tier.SILVER,
        customer_is_known=True,
        requested_discount_pct=Decimal("40"),
        net=Decimal("382.50"),
        policy=policy,
    )
    assert result.is_rejected
    assert not result.requires_approval
    assert result.rejection is not None
    assert result.rejection.reason_code == ReasonCode.DISCOUNT_ABOVE_HARD_CEILING


def test_br09_rejection_dominates_over_concurrent_approval_motives(policy) -> None:
    """Descuento sobre el techo duro Y neto sobre el umbral a la vez: BR-09
    exige que el rechazo gane y no se mezclen approval_reasons."""
    result = evaluate_policy(
        tier=Tier.STANDARD,
        customer_is_known=False,
        requested_discount_pct=Decimal("25"),
        net=Decimal("50000.00"),
        policy=policy,
    )
    assert result.is_rejected
    assert result.approval_reasons == []


def test_br09_concurrent_approval_motives_are_all_recorded(policy) -> None:
    """Cliente desconocido + descuento en excepcion + monto sobre umbral, todos
    a la vez: BR-09 exige registrar los tres, resueltos con una sola decision."""
    result = evaluate_policy(
        tier=Tier.STANDARD,
        customer_is_known=False,
        requested_discount_pct=Decimal("10"),
        net=Decimal("15000.00"),
        policy=policy,
    )
    assert not result.is_rejected
    assert result.requires_approval
    codes = {r.reason_code for r in result.approval_reasons}
    assert codes == {
        ReasonCode.UNKNOWN_CUSTOMER,
        ReasonCode.DISCOUNT_EXCEPTION,
        ReasonCode.THRESHOLD_EXCEEDED,
    }


def test_discount_exactly_at_tier_max_is_not_an_exception(policy) -> None:
    result = evaluate_policy(
        tier=Tier.GOLD,
        customer_is_known=True,
        requested_discount_pct=Decimal("12"),
        net=Decimal("100.00"),
        policy=policy,
    )
    assert not result.is_rejected
    assert result.approval_reasons == []


def test_discount_exactly_at_hard_ceiling_is_not_rejected(policy) -> None:
    """BR-07 dice '> techo duro': exactamente 20% no es rechazo."""
    result = evaluate_policy(
        tier=Tier.STANDARD,
        customer_is_known=True,
        requested_discount_pct=Decimal("20"),
        net=Decimal("100.00"),
        policy=policy,
    )
    assert not result.is_rejected


def test_net_exactly_at_threshold_does_not_require_approval(policy) -> None:
    """BR-05 dice 'neto > USD 10 000': exactamente 10,000.00 no dispara aprobacion."""
    result = evaluate_policy(
        tier=Tier.GOLD,
        customer_is_known=True,
        requested_discount_pct=Decimal("0"),
        net=Decimal("10000.00"),
        policy=policy,
    )
    assert not result.requires_approval
