"""T7 -- estado tipado del grafo. Sin LangGraph ni Postgres: solo construccion
y valores por defecto de QuoteState (PROJECT.md §4.2)."""

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.enums import DecisionAction, Outcome, ReasonCode, Tier
from app.domain.models import (
    ApprovalReason,
    Customer,
    ExtractedLineItem,
    Extraction,
    HumanDecision,
    Quote,
    ResolvedLine,
)
from app.graph.state import AuditEvent, QuoteState


def _minimal_state() -> QuoteState:
    return QuoteState(
        thread_id="thread-1",
        customer_id="FER-1001",
        raw_text="20 cascos HX-200",
    )


def test_minimal_state_only_needs_thread_customer_and_text() -> None:
    state = _minimal_state()
    assert state.thread_id == "thread-1"
    assert state.customer_id == "FER-1001"
    assert state.raw_text == "20 cascos HX-200"


def test_defaults_are_absent_not_error() -> None:
    """`None`/vacio en un campo aun no producido, nunca un valor inventado."""
    state = _minimal_state()
    assert state.extraction is None
    assert state.extraction_attempts == 0
    assert state.extraction_error is None
    assert state.customer is None
    assert state.customer_is_known is None
    assert state.tier is None
    assert state.completeness_error is None
    assert state.resolved_lines == []
    assert state.blocking_reason is None
    assert state.quote is None
    assert state.rejection_reason is None
    assert state.approval_reasons == []
    assert state.human_decision is None
    assert state.applied_decision_ids == []
    assert state.draft is None
    assert state.outcome is None
    assert state.reason_code is None
    assert state.audit_log == []


def test_state_carries_every_node_output_of_project_4_2() -> None:
    """Un estado poblado como si hubiera recorrido el grafo completo hasta
    DRAFT_READY -- confirma que cada campo de PROJECT.md §4.2 tiene lugar."""
    state = QuoteState(
        thread_id="thread-s1",
        customer_id="FER-1001",
        raw_text="20 cascos HX-200",
        extraction=Extraction(
            items=[ExtractedLineItem(product_reference="HX-200", quantity=20)],
            site="Arequipa",
            requested_discount_pct=Decimal("8"),
        ),
        extraction_attempts=1,
        customer=Customer(
            customer_id="FER-1001",
            legal_name="Andes Constructora S.A.",
            tier=Tier.GOLD,
            country="PE",
            sites=["Arequipa"],
            payment_terms_days=30,
        ),
        customer_is_known=True,
        tier=Tier.GOLD,
        resolved_lines=[
            ResolvedLine(
                sku="HX-200",
                product_name="Casco HX-200",
                quantity=20,
                unit_price=Decimal("45.00"),
                available=350,
            )
        ],
        quote=Quote(
            lines=[],
            subtotal=Decimal("900.00"),
            discount_pct=Decimal("8"),
            discount_amount=Decimal("72.00"),
            net=Decimal("828.00"),
            tax_amount=Decimal("149.04"),
            total=Decimal("977.04"),
        ),
        approval_reasons=[],
        human_decision=HumanDecision(
            decision_id="dec-1",
            action=DecisionAction.APPROVE,
            actor="jefe.ventas",
            timestamp=datetime.now(UTC),
        ),
        applied_decision_ids=["dec-1"],
        draft="Cotizacion para FER-1001: 20 x HX-200...",
        outcome=Outcome.DRAFT_READY,
        reason_code=None,
        audit_log=[AuditEvent(node="ingest", message="Solicitud registrada")],
    )
    assert state.outcome == Outcome.DRAFT_READY
    assert state.quote is not None and state.quote.total == Decimal("977.04")
    assert state.audit_log[0].node == "ingest"


def test_blocked_state_has_reason_and_no_quote() -> None:
    """BR-12/13: un bloqueo no calcula cotizacion (S5/S6 del seed)."""
    state = _minimal_state()
    state.blocking_reason = ApprovalReason(
        reason_code=ReasonCode.INSUFFICIENT_STOCK,
        detail="Disponible de RP-300: 80. Solicitado: 300.",
    )
    state.outcome = Outcome.BLOCKED
    state.reason_code = ReasonCode.INSUFFICIENT_STOCK
    assert state.quote is None
    assert state.blocking_reason.reason_code == ReasonCode.INSUFFICIENT_STOCK


def test_audit_log_reducer_is_operator_add() -> None:
    """El estado se fusiona por nodo devolviendo actualizaciones parciales;
    `audit_log` debe acumularse (Annotated + operator.add), no reemplazarse,
    para que RF-08 conserve la traza completa de la ejecucion."""
    field_info = QuoteState.model_fields["audit_log"]
    metadata_reducers = [m for m in field_info.metadata if callable(m)]
    assert metadata_reducers, "audit_log debe llevar un reducer para acumular eventos"
    reducer = metadata_reducers[0]
    combined = reducer(
        [AuditEvent(node="ingest", message="a")],
        [AuditEvent(node="extract", message="b")],
    )
    assert [e.node for e in combined] == ["ingest", "extract"]


def test_thread_id_is_required_never_regenerated_field() -> None:
    """CLAUDE.md §7: reanudar exige el mismo thread_id -- confirmar que es un
    campo de primera clase del estado, no derivado ni opcional."""
    assert "thread_id" in QuoteState.model_fields
    assert QuoteState.model_fields["thread_id"].is_required()
