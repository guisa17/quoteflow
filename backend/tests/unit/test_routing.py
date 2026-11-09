"""T10 -- routing condicional. Los seis casos de PROJECT.md §2.2 paso 4
("completo / aclaracion / SKU desconocido / sin stock / sujeto a aprobacion /
rechazo"), mas el fallo recuperable de la extraccion (RF-05)."""

from datetime import UTC, datetime

import pytest

from app.domain.enums import DecisionAction, ReasonCode
from app.domain.models import ApprovalReason, Extraction, HumanDecision
from app.graph import routing
from app.graph.state import QuoteState


def _state(**overrides) -> QuoteState:
    defaults: dict = {
        "thread_id": "thread-1",
        "customer_id": "FER-1001",
        "raw_text": "20 cascos HX-200",
    }
    defaults.update(overrides)
    return QuoteState(**defaults)


# --- route_after_extract: fallo recuperable (RF-05) --------------------------


def test_route_after_extract_success_goes_to_resolve_customer() -> None:
    update = _state(extraction=Extraction(items=[]))
    assert routing.route_after_extract(update) == routing.RESOLVE_CUSTOMER


def test_route_after_extract_failure_retries_when_attempts_remain() -> None:
    """RF-05: primer fallo -> reintenta (vuelve a 'extract')."""
    state = _state(extraction=None, extraction_attempts=1, extraction_error="esquema invalido")
    assert routing.route_after_extract(state) == routing.EXTRACT


def test_route_after_extract_failure_gives_up_after_max_attempts() -> None:
    """RF-05, fallo recuperable: agotado el reintento -> finalize
    (NEEDS_CLARIFICATION / EXTRACTION_FAILED se fija en finalize, T9)."""
    state = _state(extraction=None, extraction_attempts=2, extraction_error="esquema invalido")
    assert routing.route_after_extract(state) == routing.FINALIZE


def test_route_after_extract_never_retries_more_than_once() -> None:
    """No hay una tercera vuelta: attempts ya en el maximo no vuelve a EXTRACT."""
    state = _state(extraction=None, extraction_attempts=routing.MAX_EXTRACTION_ATTEMPTS)
    assert routing.route_after_extract(state) != routing.EXTRACT


# --- route_after_validate_request: aclaracion (BR-10/11) ---------------------


def test_route_after_validate_request_missing_info_goes_to_finalize() -> None:
    """Caso "aclaracion" (S2): informacion esencial faltante."""
    error = ApprovalReason(reason_code=ReasonCode.MISSING_QUANTITY, detail="falta cantidad")
    state = _state(completeness_error=error)
    assert routing.route_after_validate_request(state) == routing.FINALIZE


def test_route_after_validate_request_complete_goes_to_resolve_catalog() -> None:
    state = _state(completeness_error=None)
    assert routing.route_after_validate_request(state) == routing.RESOLVE_CATALOG


# --- route_after_resolve_catalog: SKU desconocido (BR-02/12) -----------------


def test_route_after_resolve_catalog_unknown_sku_goes_to_finalize() -> None:
    """Caso "SKU desconocido" (S6)."""
    reason = ApprovalReason(reason_code=ReasonCode.UNKNOWN_SKU, detail="ZZ-999 no existe")
    state = _state(blocking_reason=reason)
    assert routing.route_after_resolve_catalog(state) == routing.FINALIZE


def test_route_after_resolve_catalog_known_sku_goes_to_check_inventory() -> None:
    state = _state(blocking_reason=None)
    assert routing.route_after_resolve_catalog(state) == routing.CHECK_INVENTORY


# --- route_after_check_inventory: sin stock (BR-13) ---------------------------


def test_route_after_check_inventory_insufficient_stock_goes_to_finalize() -> None:
    """Caso "sin stock" (S5)."""
    reason = ApprovalReason(reason_code=ReasonCode.INSUFFICIENT_STOCK, detail="80 disponibles")
    state = _state(blocking_reason=reason)
    assert routing.route_after_check_inventory(state) == routing.FINALIZE


def test_route_after_check_inventory_sufficient_stock_goes_to_price_quote() -> None:
    state = _state(blocking_reason=None)
    assert routing.route_after_check_inventory(state) == routing.PRICE_QUOTE


# --- route_after_evaluate_policy: rechazo / aprobacion / completo -------------


def test_route_after_evaluate_policy_rejection_goes_to_finalize() -> None:
    """Caso "rechazo" (S8, BR-07/BR-09): nunca pasa por human_approval."""
    reason = ApprovalReason(reason_code=ReasonCode.DISCOUNT_ABOVE_HARD_CEILING, detail="40% > 20%")
    state = _state(rejection_reason=reason, approval_reasons=[])
    assert routing.route_after_evaluate_policy(state) == routing.FINALIZE


def test_route_after_evaluate_policy_approval_required_goes_to_human_approval() -> None:
    """Caso "sujeto a aprobacion" (S3/S4/S7)."""
    reasons = [ApprovalReason(reason_code=ReasonCode.THRESHOLD_EXCEEDED, detail="12900 > 10000")]
    state = _state(rejection_reason=None, approval_reasons=reasons)
    assert routing.route_after_evaluate_policy(state) == routing.HUMAN_APPROVAL


def test_route_after_evaluate_policy_clean_goes_to_compose_draft() -> None:
    """Caso "completo" (S1): dentro de politica, sin aprobacion requerida."""
    state = _state(rejection_reason=None, approval_reasons=[])
    assert routing.route_after_evaluate_policy(state) == routing.COMPOSE_DRAFT


def test_route_after_evaluate_policy_rejection_dominates_defensively() -> None:
    """BR-09: aunque hubiera approval_reasons presentes junto a un rechazo
    (no deberia ocurrir, evaluate_policy de T9 ya lo garantiza), el
    rechazo sigue dominando en el routing tambien."""
    rejection = ApprovalReason(
        reason_code=ReasonCode.DISCOUNT_ABOVE_HARD_CEILING, detail="techo duro"
    )
    approvals = [ApprovalReason(reason_code=ReasonCode.THRESHOLD_EXCEEDED, detail="monto")]
    state = _state(rejection_reason=rejection, approval_reasons=approvals)
    assert routing.route_after_evaluate_policy(state) == routing.FINALIZE


# --- route_after_apply_decision: BR-14 APPROVE/REJECT/OBSERVE ----------------


def _decision(action: DecisionAction) -> HumanDecision:
    return HumanDecision(
        decision_id="dec-1", action=action, actor="jefe.ventas", timestamp=datetime.now(UTC)
    )


def test_route_after_apply_decision_approve_goes_to_compose_draft() -> None:
    state = _state(human_decision=_decision(DecisionAction.APPROVE))
    assert routing.route_after_apply_decision(state) == routing.COMPOSE_DRAFT


def test_route_after_apply_decision_reject_goes_to_finalize() -> None:
    """AC-11: REJECT -> el caso termina (finalize resuelve el Outcome, T9)."""
    state = _state(human_decision=_decision(DecisionAction.REJECT))
    assert routing.route_after_apply_decision(state) == routing.FINALIZE


def test_route_after_apply_decision_observe_returns_to_human_approval() -> None:
    """BR-14: OBSERVE mantiene el caso en pausa -- no es un estado terminal."""
    state = _state(human_decision=_decision(DecisionAction.OBSERVE))
    assert routing.route_after_apply_decision(state) == routing.HUMAN_APPROVAL


def test_route_after_apply_decision_raises_without_decision() -> None:
    state = _state(human_decision=None)
    with pytest.raises(ValueError):
        routing.route_after_apply_decision(state)
