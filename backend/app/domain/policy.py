"""Motor de politica comercial (BR-05..BR-09).

Decide si una cotizacion pasa limpia, requiere aprobacion humana, o se
rechaza -- nunca calcula precios (eso es pricing.py) ni decide el Outcome
final del grafo (eso es routing.py en T10, que interpreta este resultado).
"""

from decimal import Decimal

from pydantic import BaseModel

from app.domain.enums import ReasonCode, Tier
from app.domain.models import ApprovalReason, Policy


class PolicyEvaluation(BaseModel):
    """Resultado de evaluar una cotizacion contra la politica comercial.

    `rejection` presente ⇒ BR-09: domina sobre cualquier motivo de aprobacion,
    `approval_reasons` queda vacio en ese caso. Sin rechazo, puede haber cero
    o varios motivos de aprobacion concurrentes (BR-09), resueltos con una
    sola decision humana.
    """

    rejection: ApprovalReason | None = None
    approval_reasons: list[ApprovalReason] = []

    @property
    def is_rejected(self) -> bool:
        return self.rejection is not None

    @property
    def requires_approval(self) -> bool:
        return not self.is_rejected and bool(self.approval_reasons)


def evaluate_policy(
    *,
    tier: Tier,
    customer_is_known: bool,
    requested_discount_pct: Decimal,
    net: Decimal,
    policy: Policy,
    manipulation_signals: list[str] | None = None,
) -> PolicyEvaluation:
    """`tier` ya viene resuelto por el caller: BR-08 exige STANDARD provisional
    cuando el cliente es desconocido, así que aquí siempre se recibe un Tier
    valido, nunca None.

    `manipulation_signals` (BR-18): si el texto intento dar ordenes al
    sistema, una persona revisa el folio. Va primero entre los motivos de
    aprobacion porque es el que la bandeja debe mostrar. Un rechazo duro
    (BR-07) sigue dominando (BR-09)."""

    if requested_discount_pct > policy.hard_discount_ceiling_pct:
        # BR-07: rechazo. Ningun humano puede aprobarlo desde el MVP.
        return PolicyEvaluation(
            rejection=ApprovalReason(
                reason_code=ReasonCode.DISCOUNT_ABOVE_HARD_CEILING,
                detail=(
                    f"Descuento solicitado {requested_discount_pct}% supera el "
                    f"techo duro de {policy.hard_discount_ceiling_pct}%."
                ),
            )
        )

    reasons: list[ApprovalReason] = []

    if manipulation_signals:
        # BR-18
        reasons.append(
            ApprovalReason(
                reason_code=ReasonCode.SUSPECTED_MANIPULATION,
                detail=(
                    "El texto intenta dar instrucciones al sistema ("
                    + "; ".join(manipulation_signals)
                    + "). Se ignoraron; revisa el pedido antes de aprobar."
                ),
            )
        )

    if not customer_is_known:
        # BR-08
        reasons.append(
            ApprovalReason(
                reason_code=ReasonCode.UNKNOWN_CUSTOMER,
                detail="Cliente no registrado; se asigno nivel STANDARD provisional.",
            )
        )

    max_discount = policy.max_discount_pct_for(tier)
    if requested_discount_pct > max_discount:
        # BR-06
        reasons.append(
            ApprovalReason(
                reason_code=ReasonCode.DISCOUNT_EXCEPTION,
                detail=(
                    f"Descuento solicitado {requested_discount_pct}% supera el "
                    f"máximo de {tier.value} ({max_discount}%)."
                ),
            )
        )

    if net > policy.approval_threshold_usd:
        # BR-05
        reasons.append(
            ApprovalReason(
                reason_code=ReasonCode.THRESHOLD_EXCEEDED,
                detail=(
                    f"Neto {net} supera el umbral de aprobación de {policy.approval_threshold_usd}."
                ),
            )
        )

    return PolicyEvaluation(rejection=None, approval_reasons=reasons)
