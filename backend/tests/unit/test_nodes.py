"""T9 -- los 12 nodos del grafo, cada uno probado en aislamiento (sin grafo
compilado, salvo `human_approval`: `interrupt()` exige un contexto de
ejecucion de LangGraph, asi que se prueba envuelto en un grafo minimo de un
solo nodo -- sigue siendo "en aislamiento" del resto de los 11 nodos)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.domain.enums import DecisionAction, Outcome, ReasonCode, Tier
from app.domain.models import (
    ApprovalReason,
    ExtractedLineItem,
    Extraction,
    HumanDecision,
    ResolvedLine,
)
from app.graph import nodes
from app.graph.state import QuoteState
from app.llm.fake_extractor import FakeExtractor


def _state(**overrides) -> QuoteState:
    defaults: dict = {
        "thread_id": "thread-1",
        "customer_id": "FER-1001",
        "raw_text": "  20 cascos HX-200  ",
    }
    defaults.update(overrides)
    return QuoteState(**defaults)


# --- ingest -------------------------------------------------------------


async def test_ingest_strips_raw_text_and_logs_audit() -> None:
    update = await nodes.ingest(_state(raw_text="  20 cascos HX-200  "))
    assert update["raw_text"] == "20 cascos HX-200"
    assert update["audit_log"][0].node == "ingest"


# --- extract --------------------------------------------------------------


async def test_extract_node_records_successful_extraction() -> None:
    extract = nodes.make_extract_node(FakeExtractor())
    update = await extract(_state(raw_text="Necesito 20 cascos HX-200"))
    assert update["extraction"].items[0].product_reference == "HX-200"
    assert update["extraction_attempts"] == 1
    assert update["extraction_error"] is None


async def test_extract_node_records_failure_and_increments_attempts() -> None:
    """RF-05: el nodo registra el fallo; el reintento es responsabilidad de
    routing.py (T10), no de este nodo."""
    extract = nodes.make_extract_node(FakeExtractor(force_failure=True))
    update = await extract(_state(extraction_attempts=1))
    assert update["extraction_attempts"] == 2
    assert update["extraction_error"] is not None
    assert "extraction" not in update


# --- resolve_customer -----------------------------------------------------


async def test_resolve_customer_known_customer_sets_tier() -> None:
    update = await nodes.resolve_customer(_state(customer_id="FER-1001"))
    assert update["customer_is_known"] is True
    assert update["tier"] == Tier.GOLD
    assert update["customer"] is not None


async def test_resolve_customer_unknown_customer_defaults_to_standard() -> None:
    """BR-08: cliente desconocido -> STANDARD provisional, no bloqueo."""
    update = await nodes.resolve_customer(_state(customer_id="FER-9999"))
    assert update["customer_is_known"] is False
    assert update["tier"] == Tier.STANDARD
    assert update["customer"] is None
    assert update["audit_log"][0].reason_code == ReasonCode.UNKNOWN_CUSTOMER


# --- validate_request -------------------------------------------------------


async def test_validate_request_raises_without_extraction() -> None:
    with pytest.raises(ValueError):
        await nodes.validate_request(_state())


async def test_validate_request_missing_quantity_blocks() -> None:
    """BR-10 / S2: sin cantidad, NEEDS_CLARIFICATION antes de calcular nada."""
    extraction = Extraction(items=[ExtractedLineItem(product_reference="HX-200", quantity=None)])
    update = await nodes.validate_request(_state(extraction=extraction))
    assert update["completeness_error"].reason_code == ReasonCode.MISSING_QUANTITY


async def test_validate_request_complete_extraction_passes() -> None:
    extraction = Extraction(items=[ExtractedLineItem(product_reference="HX-200", quantity=20)])
    update = await nodes.validate_request(_state(extraction=extraction))
    assert update["completeness_error"] is None


# --- resolve_catalog --------------------------------------------------------


async def test_resolve_catalog_unknown_sku_blocks() -> None:
    """BR-02 / BR-12 / S6: SKU inexistente, sin sustitucion."""
    extraction = Extraction(items=[ExtractedLineItem(product_reference="ZZ-999", quantity=50)])
    update = await nodes.resolve_catalog(_state(extraction=extraction))
    assert update["blocking_reason"].reason_code == ReasonCode.UNKNOWN_SKU


async def test_resolve_catalog_known_sku_passes() -> None:
    extraction = Extraction(items=[ExtractedLineItem(product_reference="HX-200", quantity=20)])
    update = await nodes.resolve_catalog(_state(extraction=extraction))
    assert update["blocking_reason"] is None


# --- check_inventory ---------------------------------------------------------


async def test_check_inventory_insufficient_stock_blocks() -> None:
    """BR-13 / S5: RP-300 disponible 80 < 300 solicitados."""
    extraction = Extraction(items=[ExtractedLineItem(product_reference="RP-300", quantity=300)])
    update = await nodes.check_inventory(_state(extraction=extraction))
    assert update["blocking_reason"].reason_code == ReasonCode.INSUFFICIENT_STOCK
    assert "80" in update["blocking_reason"].detail
    assert update["resolved_lines"] == []


async def test_check_inventory_builds_resolved_lines() -> None:
    """S1: HX-200 x20, dentro de stock -> linea resuelta con precio y disponible."""
    extraction = Extraction(items=[ExtractedLineItem(product_reference="HX-200", quantity=20)])
    update = await nodes.check_inventory(_state(extraction=extraction))
    assert update["blocking_reason"] is None
    line = update["resolved_lines"][0]
    assert line.sku == "HX-200"
    assert line.quantity == 20
    assert line.unit_price == Decimal("45.00")
    assert line.available >= 20


# --- price_quote --------------------------------------------------------------


async def test_price_quote_reproduces_ac01_exactly() -> None:
    """AC-01: 20 x 45.00 = 900.00 -> 8% -> 828.00 -> IGV 149.04 -> 977.04."""
    resolved = [
        ResolvedLine(
            sku="HX-200",
            product_name="Casco HX-200",
            quantity=20,
            unit_price=Decimal("45.00"),
            available=350,
        )
    ]
    extraction = Extraction(items=[], requested_discount_pct=Decimal("8"))
    update = await nodes.price_quote(_state(extraction=extraction, resolved_lines=resolved))
    quote = update["quote"]
    assert quote.subtotal == Decimal("900.00")
    assert quote.discount_amount == Decimal("72.00")
    assert quote.net == Decimal("828.00")
    assert quote.tax_amount == Decimal("149.04")
    assert quote.total == Decimal("977.04")


async def test_price_quote_defaults_missing_discount_to_zero() -> None:
    """BR-11: descuento ausente en la extraccion = 0%."""
    resolved = [
        ResolvedLine(
            sku="AR-450",
            product_name="Arnes",
            quantity=60,
            unit_price=Decimal("215.00"),
            available=80,
        )
    ]
    extraction = Extraction(items=[])  # requested_discount_pct=None por defecto
    update = await nodes.price_quote(_state(extraction=extraction, resolved_lines=resolved))
    assert update["quote"].discount_pct == Decimal("0")
    assert update["quote"].net == Decimal("12900.00")


# --- evaluate_policy -----------------------------------------------------------


async def test_evaluate_policy_within_policy_requires_no_approval() -> None:
    from app.domain.models import Quote

    quote = Quote(
        lines=[],
        subtotal=Decimal("900.00"),
        discount_pct=Decimal("8"),
        discount_amount=Decimal("72.00"),
        net=Decimal("828.00"),
        tax_amount=Decimal("149.04"),
        total=Decimal("977.04"),
    )
    extraction = Extraction(items=[], requested_discount_pct=Decimal("8"))
    update = await nodes.evaluate_policy(
        _state(extraction=extraction, quote=quote, tier=Tier.GOLD, customer_is_known=True)
    )
    assert update["rejection_reason"] is None
    assert update["approval_reasons"] == []


async def test_evaluate_policy_threshold_exceeded_requires_approval() -> None:
    """S3: neto 12900.00 > 10000 -> THRESHOLD_EXCEEDED."""
    from app.domain.models import Quote

    quote = Quote(
        lines=[],
        subtotal=Decimal("12900.00"),
        discount_pct=Decimal("0"),
        discount_amount=Decimal("0.00"),
        net=Decimal("12900.00"),
        tax_amount=Decimal("2322.00"),
        total=Decimal("15222.00"),
    )
    extraction = Extraction(items=[])
    update = await nodes.evaluate_policy(
        _state(extraction=extraction, quote=quote, tier=Tier.GOLD, customer_is_known=True)
    )
    codes = {r.reason_code for r in update["approval_reasons"]}
    assert codes == {ReasonCode.THRESHOLD_EXCEEDED}


async def test_evaluate_policy_hard_ceiling_rejects_never_pending() -> None:
    """S8: 40% > techo duro 20% -> REJECTED, nunca aprobacion (BR-07/BR-09)."""
    from app.domain.models import Quote

    quote = Quote(
        lines=[],
        subtotal=Decimal("637.50"),
        discount_pct=Decimal("40"),
        discount_amount=Decimal("255.00"),
        net=Decimal("382.50"),
        tax_amount=Decimal("68.85"),
        total=Decimal("451.35"),
    )
    extraction = Extraction(items=[], requested_discount_pct=Decimal("40"))
    update = await nodes.evaluate_policy(
        _state(extraction=extraction, quote=quote, tier=Tier.SILVER, customer_is_known=True)
    )
    assert update["rejection_reason"].reason_code == ReasonCode.DISCOUNT_ABOVE_HARD_CEILING
    assert update["approval_reasons"] == []


async def test_evaluate_policy_raises_without_quote() -> None:
    with pytest.raises(ValueError):
        await nodes.evaluate_policy(_state(tier=Tier.GOLD, customer_is_known=True))


# --- human_approval (requiere contexto de grafo para interrupt()) ------------


def _single_node_graph(node_fn):
    builder = StateGraph(QuoteState)
    builder.add_node("n", node_fn)
    builder.add_edge(START, "n")
    builder.add_edge("n", END)
    return builder.compile(checkpointer=MemorySaver())


async def test_human_approval_pauses_and_resumes_with_decision() -> None:
    graph = _single_node_graph(nodes.human_approval)
    config = {"configurable": {"thread_id": "t-human-approval"}}
    reasons = [ApprovalReason(reason_code=ReasonCode.THRESHOLD_EXCEEDED, detail="d")]
    state = _state(approval_reasons=reasons)

    paused = await graph.ainvoke(state, config=config)
    assert "__interrupt__" in paused
    assert paused["__interrupt__"][0].value["thread_id"] == "thread-1"

    decision_payload = {
        "decision_id": "dec-1",
        "action": "APPROVE",
        "actor": "jefe.ventas",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    resumed = await graph.ainvoke(Command(resume=decision_payload), config=config)
    assert resumed["human_decision"].decision_id == "dec-1"
    assert resumed["human_decision"].action == DecisionAction.APPROVE


# --- apply_decision -------------------------------------------------------------


async def test_apply_decision_raises_without_human_decision() -> None:
    with pytest.raises(ValueError):
        await nodes.apply_decision(_state())


async def test_apply_decision_records_new_decision() -> None:
    decision = HumanDecision(
        decision_id="dec-1",
        action=DecisionAction.APPROVE,
        actor="jefe.ventas",
        timestamp=datetime.now(UTC),
    )
    update = await nodes.apply_decision(_state(human_decision=decision))
    assert update["applied_decision_ids"] == ["dec-1"]


async def test_apply_decision_is_idempotent_for_repeated_decision_id() -> None:
    """BR-15: reenviar un decision_id ya aplicado no produce efecto adicional."""
    decision = HumanDecision(
        decision_id="dec-1",
        action=DecisionAction.APPROVE,
        actor="jefe.ventas",
        timestamp=datetime.now(UTC),
    )
    update = await nodes.apply_decision(
        _state(human_decision=decision, applied_decision_ids=["dec-1"])
    )
    assert "applied_decision_ids" not in update
    assert "ya aplicado" in update["audit_log"][0].message


# --- compose_draft ----------------------------------------------------------------


async def test_compose_draft_includes_totals_from_quote() -> None:
    from app.domain.models import Quote

    line = ResolvedLine(
        sku="HX-200",
        product_name="Casco HX-200",
        quantity=20,
        unit_price=Decimal("45.00"),
        available=350,
    )
    quote = Quote(
        lines=[line],
        subtotal=Decimal("900.00"),
        discount_pct=Decimal("8"),
        discount_amount=Decimal("72.00"),
        net=Decimal("828.00"),
        tax_amount=Decimal("149.04"),
        total=Decimal("977.04"),
    )
    update = await nodes.compose_draft(_state(quote=quote))
    assert "977.04" in update["draft"]
    assert "HX-200" in update["draft"]


async def test_compose_draft_raises_without_quote() -> None:
    with pytest.raises(ValueError):
        await nodes.compose_draft(_state())


# --- finalize -----------------------------------------------------------------------


async def test_finalize_draft_ready_when_nothing_blocking() -> None:
    update = await nodes.finalize(_state())
    assert update["outcome"] == Outcome.DRAFT_READY
    assert update["reason_code"] is None


async def test_finalize_needs_clarification_on_extraction_failure() -> None:
    update = await nodes.finalize(_state(extraction=None, extraction_error="boom"))
    assert update["outcome"] == Outcome.NEEDS_CLARIFICATION
    assert update["reason_code"] == ReasonCode.EXTRACTION_FAILED


async def test_finalize_needs_clarification_on_completeness_error() -> None:
    error = ApprovalReason(reason_code=ReasonCode.MISSING_QUANTITY, detail="falta cantidad")
    update = await nodes.finalize(_state(completeness_error=error))
    assert update["outcome"] == Outcome.NEEDS_CLARIFICATION
    assert update["reason_code"] == ReasonCode.MISSING_QUANTITY


async def test_finalize_blocked_on_blocking_reason() -> None:
    error = ApprovalReason(reason_code=ReasonCode.INSUFFICIENT_STOCK, detail="sin stock")
    update = await nodes.finalize(_state(blocking_reason=error))
    assert update["outcome"] == Outcome.BLOCKED
    assert update["reason_code"] == ReasonCode.INSUFFICIENT_STOCK


async def test_finalize_rejected_by_policy_on_rejection_reason() -> None:
    error = ApprovalReason(reason_code=ReasonCode.DISCOUNT_ABOVE_HARD_CEILING, detail="techo duro")
    update = await nodes.finalize(_state(rejection_reason=error))
    assert update["outcome"] == Outcome.REJECTED_BY_POLICY
    assert update["reason_code"] == ReasonCode.DISCOUNT_ABOVE_HARD_CEILING


async def test_finalize_human_reject_maps_to_rejected_by_policy() -> None:
    """BR-14: decision REJECT tambien termina en rechazo. Decision de diseno
    documentada: el dominio (T2-T6) no define un Outcome separado para
    rechazo humano, asi que se reutiliza REJECTED_BY_POLICY."""
    reasons = [ApprovalReason(reason_code=ReasonCode.DISCOUNT_EXCEPTION, detail="d")]
    decision = HumanDecision(
        decision_id="dec-1",
        action=DecisionAction.REJECT,
        actor="jefe.ventas",
        timestamp=datetime.now(UTC),
    )
    update = await nodes.finalize(_state(approval_reasons=reasons, human_decision=decision))
    assert update["outcome"] == Outcome.REJECTED_BY_POLICY
    assert update["reason_code"] == ReasonCode.DISCOUNT_EXCEPTION
