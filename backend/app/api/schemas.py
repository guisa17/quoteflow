"""Esquemas HTTP (RF-01..RF-04), forma exacta fijada en docs/API_CONTRACT.md.

Deliberadamente separados de app/domain/models.py: el contrato de red usa
string decimal para dinero (nunca float/number, misma razon que BR-04
aplicada al borde de red), mientras que el dominio usa `Decimal`. Esta capa
es la unica que traduce entre ambos -- ADR-002/CLAUDE.md §2: app/api/
expone y serializa, no contiene reglas.
"""

from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.domain.enums import DecisionAction, Outcome, ReasonCode

# BR-20: limites tecnicos de entrada, no valores de dominio.
_CustomerId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
_RawText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000)]
_DecisionId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
_Actor = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=254)]
_Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2_000)]


class ApprovalReasonOut(BaseModel):
    reason_code: ReasonCode
    detail: str


class ExtractedLineItemOut(BaseModel):
    product_reference: str
    quantity: int | None


class ExtractionOut(BaseModel):
    items: list[ExtractedLineItemOut]
    site: str | None
    requested_date: str | None
    requested_discount_pct: str | None
    # Quien leyo el texto: modelo de Gemini o "reglas locales (respaldo: ...)".
    source: str | None = None


class QuoteLineOut(BaseModel):
    sku: str
    product_name: str
    quantity: int
    unit_price: str
    line_subtotal: str


class QuoteOut(BaseModel):
    lines: list[QuoteLineOut]
    subtotal: str
    discount_pct: str
    discount_amount: str
    net: str
    tax_amount: str
    total: str
    currency: str


class AuditEventOut(BaseModel):
    node: str
    timestamp: str
    note: str
    reason_code: str | None = None


class HumanDecisionOut(BaseModel):
    decision_id: str
    action: DecisionAction
    actor: str
    comment: str | None
    timestamp: str


class CreateRequestBody(BaseModel):
    customer_id: _CustomerId
    raw_text: _RawText


class RequestSummary(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    summary: str
    outcome: Outcome
    reason_code: ReasonCode | None
    updated_at: str


class RequestDetail(BaseModel):
    id: str
    thread_id: str
    customer_id: str
    customer_name: str
    raw_text: str
    outcome: Outcome

    extraction: ExtractionOut | None
    quote: QuoteOut | None
    approval_reasons: list[ApprovalReasonOut]
    rejection_reason: ApprovalReasonOut | None
    blocking_reason: ApprovalReasonOut | None

    audit_trail: list[AuditEventOut]
    human_decision: HumanDecisionOut | None
    draft_text: str | None

    created_at: str
    updated_at: str


class DecisionBody(BaseModel):
    decision_id: _DecisionId
    action: DecisionAction
    actor: _Actor
    comment: _Comment | None = None
