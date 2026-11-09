"""Traduce `QuoteState` (dominio/grafo) + la fila de cache (store.py) a los
esquemas HTTP del contrato (RF-03/RF-04). Unico lugar donde se decide como
se ve una solicitud desde afuera -- ADR-002/CLAUDE.md §2: expone y
serializa, no decide."""

from decimal import ROUND_HALF_UP, Decimal

from app.api.schemas import (
    ApprovalReasonOut,
    AuditEventOut,
    ExtractedLineItemOut,
    ExtractionOut,
    HumanDecisionOut,
    QuoteLineOut,
    QuoteOut,
    RequestDetail,
)
from app.domain.enums import Outcome, ReasonCode
from app.graph.state import QuoteState

_CENTS = Decimal("0.01")


def _money(value: Decimal) -> str:
    return str(value)


def _line_subtotal(unit_price: Decimal, quantity: int) -> str:
    """Recalculo de presentacion (RF-06): ResolvedLine no persiste el
    subtotal de linea (T2, deliberado -- ver models.py). Mismo redondeo
    que pricing.py, para que la cifra mostrada coincida con la ya usada
    al calcular subtotal/neto/total."""
    return str((unit_price * quantity).quantize(_CENTS, rounding=ROUND_HALF_UP))


def summarize(state: QuoteState) -> str:
    """Resumen corto para la bandeja, ej. '20 x HX-200'."""
    if state.extraction is None or not state.extraction.items:
        return state.raw_text[:60]
    parts = [
        f"{item.quantity if item.quantity is not None else '?'} x {item.product_reference}"
        for item in state.extraction.items
    ]
    return ", ".join(parts)


def is_paused(snapshot_next: tuple[str, ...]) -> bool:
    return snapshot_next == ("human_approval",)


def resolve_outcome(state: QuoteState, paused: bool) -> Outcome:
    """`PENDING_APPROVAL` es un estado observado (el grafo esta pausado),
    no algo que `finalize` escriba -- ver ADR-002/PROJECT.md §4.2: solo
    finalize fija `state.outcome`, y no corre mientras el caso esta en
    `human_approval`."""
    if paused:
        return Outcome.PENDING_APPROVAL
    if state.outcome is not None:
        return state.outcome
    raise ValueError("Estado del grafo sin outcome y sin pausa -- estado inconsistente.")


def resolve_reason_code(state: QuoteState, outcome: Outcome) -> ReasonCode | None:
    if outcome == Outcome.PENDING_APPROVAL:
        return state.approval_reasons[0].reason_code if state.approval_reasons else None
    return state.reason_code


def resolve_blocking_reason(state: QuoteState, outcome: Outcome) -> ApprovalReasonOut | None:
    """BLOCKED puede venir de BR-12/13 (`blocking_reason`); NEEDS_CLARIFICATION
    puede venir de BR-10/11 (`completeness_error`) o de un fallo de
    extraccion (RF-05, sin ApprovalReason propio -- se sintetiza aqui)."""
    if outcome not in (Outcome.BLOCKED, Outcome.NEEDS_CLARIFICATION):
        return None
    if state.blocking_reason is not None:
        return ApprovalReasonOut(
            reason_code=state.blocking_reason.reason_code, detail=state.blocking_reason.detail
        )
    if state.completeness_error is not None:
        return ApprovalReasonOut(
            reason_code=state.completeness_error.reason_code,
            detail=state.completeness_error.detail,
        )
    if state.extraction_error is not None:
        return ApprovalReasonOut(
            reason_code=ReasonCode.EXTRACTION_FAILED, detail=state.extraction_error
        )
    return None


def to_request_detail(
    *,
    id_: str,
    state: QuoteState,
    customer_name: str,
    paused: bool,
    created_at: str,
    updated_at: str,
) -> RequestDetail:
    outcome = resolve_outcome(state, paused)

    extraction_out = None
    if state.extraction is not None:
        extraction_out = ExtractionOut(
            items=[
                ExtractedLineItemOut(product_reference=i.product_reference, quantity=i.quantity)
                for i in state.extraction.items
            ],
            site=state.extraction.site,
            requested_date=state.extraction.requested_date,
            requested_discount_pct=(
                _money(state.extraction.requested_discount_pct)
                if state.extraction.requested_discount_pct is not None
                else None
            ),
        )

    quote_out = None
    if state.quote is not None:
        quote_out = QuoteOut(
            lines=[
                QuoteLineOut(
                    sku=line.sku,
                    product_name=line.product_name,
                    quantity=line.quantity,
                    unit_price=_money(line.unit_price),
                    line_subtotal=_line_subtotal(line.unit_price, line.quantity),
                )
                for line in state.quote.lines
            ],
            subtotal=_money(state.quote.subtotal),
            discount_pct=_money(state.quote.discount_pct),
            discount_amount=_money(state.quote.discount_amount),
            net=_money(state.quote.net),
            tax_amount=_money(state.quote.tax_amount),
            total=_money(state.quote.total),
            currency=state.quote.currency,
        )

    human_decision_out = None
    if state.human_decision is not None:
        human_decision_out = HumanDecisionOut(
            decision_id=state.human_decision.decision_id,
            action=state.human_decision.action,
            actor=state.human_decision.actor,
            comment=state.human_decision.comment,
            timestamp=state.human_decision.timestamp.isoformat(),
        )

    return RequestDetail(
        id=id_,
        thread_id=state.thread_id,
        customer_id=state.customer_id,
        customer_name=customer_name,
        raw_text=state.raw_text,
        outcome=outcome,
        extraction=extraction_out,
        quote=quote_out,
        approval_reasons=(
            [
                ApprovalReasonOut(reason_code=r.reason_code, detail=r.detail)
                for r in state.approval_reasons
            ]
            if outcome == Outcome.PENDING_APPROVAL
            else []
        ),
        rejection_reason=(
            ApprovalReasonOut(
                reason_code=state.rejection_reason.reason_code,
                detail=state.rejection_reason.detail,
            )
            if state.rejection_reason is not None
            else None
        ),
        blocking_reason=resolve_blocking_reason(state, outcome),
        audit_trail=[
            AuditEventOut(node=e.node, timestamp=e.timestamp.isoformat(), note=e.message)
            for e in state.audit_log
        ],
        human_decision=human_decision_out,
        draft_text=state.draft,
        created_at=created_at,
        updated_at=updated_at,
    )
