"""Los 12 nodos del grafo (T9, PROJECT.md §4.2).

Cada nodo es `async def nodo(state: QuoteState) -> dict`: LangGraph fusiona
el dict devuelto contra el estado (T7) campo a campo. Ningun nodo decide una
regla nueva -- solo orquesta: llama a las cinco herramientas de dominio
(`app/domain/tools.py`, T9) o a las funciones ya probadas de T4-T6
(`pricing.calculate_quote`, `policy.evaluate_policy`,
`validation.check_completeness`), y traduce el resultado a campos del
estado. Ver ADR-002 y CLAUDE.md §2: `app/graph/` orquesta, no contiene
logica de negocio propia.

**Orden de ejecucion real** (distinto del orden de la tabla de PROJECT.md
§4.2, que agrupa por responsabilidad, no por secuencia): `validate_request`
corre *antes* que `resolve_catalog`/`check_inventory`. Es el orden que exige
la propia documentacion de `validation.py` (T6): "la completitud se verifica
sobre la extraccion cruda, antes de tocar catalogo o inventario (BR-10/11);
la resolucion de SKU y stock ocurre despues (BR-12/13)". Verificar cantidad
antes de resolver SKU evita una consulta al catalogo que BR-10 ya haria
inutil. El orden final:

`ingest -> extract -> resolve_customer -> validate_request -> resolve_catalog
-> check_inventory -> price_quote -> evaluate_policy -> human_approval ->
apply_decision -> compose_draft -> finalize`

Las rutas condicionales entre ellos son responsabilidad de `routing.py` (T10).
"""

from collections import Counter
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

from langgraph.types import interrupt

from app.domain.enums import DecisionAction, Outcome, ReasonCode, Tier
from app.domain.manipulation import detect_manipulation
from app.domain.models import ApprovalReason, HumanDecision, ResolvedLine
from app.domain.policy import evaluate_policy as evaluate_policy_rule
from app.domain.pricing import calculate_quote
from app.domain.tools import (
    check_availability,
    get_policy,
    get_unit_price,
    lookup_customer,
    lookup_product,
)
from app.domain.validation import check_completeness
from app.graph.state import AuditEvent, QuoteState
from app.llm.base import ExtractionError, Extractor

NodeFn = Callable[[QuoteState], Awaitable[dict[str, Any]]]


async def ingest(state: QuoteState) -> dict[str, Any]:
    """Normaliza la solicitud y abre el registro de auditoria (RF-08).

    `thread_id` ya llega fijado por quien crea el estado inicial (la API,
    fuera de T7-T11) -- este nodo nunca lo genera ni lo reemplaza
    (CLAUDE.md §7: reanudar exige el mismo thread_id siempre)."""
    return {
        "raw_text": state.raw_text.strip(),
        "audit_log": [
            AuditEvent(
                node="ingest",
                message=(
                    f"Solicitud registrada para {state.customer_id} (thread {state.thread_id})."
                ),
            )
        ],
    }


def make_extract_node(extractor: Extractor) -> NodeFn:
    """RF-05: un intento de extraccion por invocacion de este nodo.

    El reintento (una vez) y la degradacion a `NEEDS_CLARIFICATION` /
    `EXTRACTION_FAILED` cuando persiste el fallo son responsabilidad de las
    rutas condicionales (T10): LangGraph reejecuta el nodo desde el inicio
    en cada paso del grafo, asi que cada llamada aqui ya es "un intento".

    Factory en vez de funcion plana porque el extractor es una dependencia
    externa (fake en pruebas, real fuera del alcance de T7-T11, ver
    LOOP.md) que `app/graph/build.py` (T11) decide segun `settings.llm_mode`.
    """

    async def extract(state: QuoteState) -> dict[str, Any]:
        attempts = state.extraction_attempts + 1
        try:
            extraction = await extractor.extract(state.raw_text)
        except ExtractionError as exc:
            return {
                "extraction_attempts": attempts,
                "extraction_error": str(exc),
                "audit_log": [
                    AuditEvent(
                        node="extract",
                        message=f"Intento {attempts}: fallo de extraccion -- {exc}",
                        reason_code=ReasonCode.EXTRACTION_FAILED,
                    )
                ],
            }
        audit = [
            AuditEvent(
                node="extract",
                message=(
                    f"Intento {attempts}: {len(extraction.items)} item(s) extraido(s)"
                    + (f" con {extraction.source}." if extraction.source else ".")
                ),
            )
        ]
        # BR-18: el ataque ya no puede cambiar precio, nivel ni aprobacion
        # (BR-17), pero tampoco debe pasar desapercibido.
        signals = detect_manipulation(state.raw_text)
        if extraction.injection_suspected:
            signals.append("el modelo de lectura detecto instrucciones al sistema")
        if signals:
            audit.append(
                AuditEvent(
                    node="extract",
                    message=(
                        "Posible manipulacion en el texto del cliente: "
                        + "; ".join(signals)
                        + ". Las instrucciones se ignoraron (BR-17)."
                    ),
                    reason_code=ReasonCode.SUSPECTED_MANIPULATION,
                )
            )
        return {
            "extraction": extraction,
            "extraction_attempts": attempts,
            "extraction_error": None,
            "manipulation_signals": signals,
            "audit_log": audit,
        }

    return extract


async def resolve_customer(state: QuoteState) -> dict[str, Any]:
    """BR-08: cliente no registrado -> tier STANDARD provisional + revision
    humana. `lookup_customer` es la unica fuente del nivel -- nunca sale de
    la extraccion (BR-03/ADR-002 §2: ese campo ya fue descartado ahi)."""
    customer = lookup_customer(state.customer_id)
    if customer is None:
        return {
            "customer": None,
            "customer_is_known": False,
            "tier": Tier.STANDARD,
            "audit_log": [
                AuditEvent(
                    node="resolve_customer",
                    message=(
                        f"Cliente {state.customer_id} no registrado; "
                        "tier STANDARD provisional (BR-08)."
                    ),
                    reason_code=ReasonCode.UNKNOWN_CUSTOMER,
                )
            ],
        }
    return {
        "customer": customer,
        "customer_is_known": True,
        "tier": customer.tier,
        "audit_log": [
            AuditEvent(
                node="resolve_customer",
                message=f"Cliente {state.customer_id} resuelto: tier {customer.tier.value}.",
            )
        ],
    }


async def validate_request(state: QuoteState) -> dict[str, Any]:
    """BR-10/BR-11: completitud sobre la extraccion cruda -- antes de
    resolver catalogo o inventario. Asume que `extract` ya corrio con exito;
    las rutas condicionales (T10) no llegan aqui si la extraccion fallo."""
    if state.extraction is None:
        raise ValueError("validate_request requiere una extraccion ya establecida por 'extract'")

    result = check_completeness(state.extraction)
    if not result.ok:
        reason = result.blocking_reason
        assert reason is not None  # invariante de check_completeness: ok=False => hay motivo
        return {
            "completeness_error": reason,
            "audit_log": [
                AuditEvent(
                    node="validate_request", message=reason.detail, reason_code=reason.reason_code
                )
            ],
        }
    return {
        "completeness_error": None,
        "audit_log": [
            AuditEvent(node="validate_request", message="Solicitud completa (BR-10/11).")
        ],
    }


async def resolve_catalog(state: QuoteState) -> dict[str, Any]:
    """BR-02/BR-12: coincidencia exacta contra el catalogo, sin sustitucion
    por similitud. El primer SKU no encontrado detiene toda la solicitud --
    BR-12 dice explicitamente "no se cotizan parcialmente los items
    restantes", asi que no se acumulan errores de varios items."""
    if state.extraction is None:
        raise ValueError("resolve_catalog requiere una extraccion ya establecida por 'extract'")

    for item in state.extraction.items:
        if lookup_product(item.product_reference) is None:
            reason = ApprovalReason(
                reason_code=ReasonCode.UNKNOWN_SKU,
                detail=f"'{item.product_reference}' no existe en el catalogo o esta inactivo.",
            )
            return {
                "blocking_reason": reason,
                "audit_log": [
                    AuditEvent(
                        node="resolve_catalog",
                        message=reason.detail,
                        reason_code=reason.reason_code,
                    )
                ],
            }

    return {
        "blocking_reason": None,
        "audit_log": [
            AuditEvent(
                node="resolve_catalog",
                message=(
                    f"{len(state.extraction.items)} item(s) resuelto(s) contra el catalogo (BR-02)."
                ),
            )
        ],
    }


async def check_inventory(state: QuoteState) -> dict[str, Any]:
    """BR-13: disponible = on_hand - reserved (unico stock cotizable).

    Construye aqui las `ResolvedLine` finales: necesita nombre y precio
    (`lookup_product`/`get_unit_price`) y disponibilidad (`check_availability`)
    juntos para que la linea quede completa, lista para `pricing.py`. Asume
    que `resolve_catalog` ya confirmo que cada SKU existe. La disponibilidad se
    compara con la cantidad acumulada por SKU: repetir un SKU en varias lineas
    no permite superar el stock (BR-13)."""
    if state.extraction is None:
        raise ValueError("check_inventory requiere una extraccion ya establecida por 'extract'")

    resolved: list[ResolvedLine] = []
    requested: Counter[str] = Counter()
    for item in state.extraction.items:
        quantity = item.quantity or 0
        product = lookup_product(item.product_reference)
        if product is None:
            # Defensivo: resolve_catalog ya deberia haber detenido la ruta
            # antes de llegar aqui. No es un caso de negocio nuevo.
            reason = ApprovalReason(
                reason_code=ReasonCode.UNKNOWN_SKU,
                detail=f"'{item.product_reference}' no existe en el catalogo o esta inactivo.",
            )
            return {
                "blocking_reason": reason,
                "resolved_lines": [],
                "audit_log": [
                    AuditEvent(
                        node="check_inventory",
                        message=reason.detail,
                        reason_code=reason.reason_code,
                    )
                ],
            }

        requested[product.sku] += quantity
        availability = check_availability(product.sku, requested[product.sku])
        price = get_unit_price(product.sku)
        if availability is None or price is None or not availability.covers_quantity:
            available_qty = availability.available if availability is not None else 0
            reason = ApprovalReason(
                reason_code=ReasonCode.INSUFFICIENT_STOCK,
                detail=(
                    f"Disponible de {product.sku}: {available_qty}. "
                    f"Solicitado: {requested[product.sku]}."
                ),
            )
            return {
                "blocking_reason": reason,
                "resolved_lines": [],
                "audit_log": [
                    AuditEvent(
                        node="check_inventory",
                        message=reason.detail,
                        reason_code=reason.reason_code,
                    )
                ],
            }

        resolved.append(
            ResolvedLine(
                sku=product.sku,
                product_name=product.name,
                quantity=quantity,
                unit_price=price,
                available=availability.available,
            )
        )

    return {
        "resolved_lines": resolved,
        "blocking_reason": None,
        "audit_log": [
            AuditEvent(
                node="check_inventory",
                message=f"Stock suficiente para {len(resolved)} linea(s) (BR-13).",
            )
        ],
    }


async def price_quote(state: QuoteState) -> dict[str, Any]:
    """RF-06/BR-04: calculo determinista sobre las lineas ya resueltas.

    BR-11: descuento ausente en la extraccion se trata como 0% -- el
    porcentaje solicitado todavia no fue validado contra politica, eso
    ocurre despues en `evaluate_policy`; aqui solo se cotiza con lo pedido."""
    policy = get_policy()
    discount_pct = _requested_discount_pct(state)
    quote = calculate_quote(
        lines=state.resolved_lines,
        discount_pct=discount_pct,
        tax_rate=policy.tax.rate,
        currency=policy.currency,
    )
    return {
        "quote": quote,
        "audit_log": [
            AuditEvent(
                node="price_quote",
                message=(
                    f"Cotizado: subtotal {quote.subtotal} neto {quote.net} total {quote.total}."
                ),
            )
        ],
    }


async def evaluate_policy(state: QuoteState) -> dict[str, Any]:
    """BR-05..BR-09. Reusa `app.domain.policy.evaluate_policy` (T5) tal
    cual -- este nodo solo junta sus insumos desde el estado y traduce el
    resultado a los campos correspondientes."""
    if state.quote is None:
        raise ValueError("evaluate_policy requiere una cotizacion ya calculada por 'price_quote'")
    if state.tier is None or state.customer_is_known is None:
        raise ValueError("evaluate_policy requiere tier/customer_is_known ya resueltos")

    policy = get_policy()
    discount_pct = _requested_discount_pct(state)
    result = evaluate_policy_rule(
        tier=state.tier,
        customer_is_known=state.customer_is_known,
        requested_discount_pct=discount_pct,
        net=state.quote.net,
        policy=policy,
        manipulation_signals=state.manipulation_signals,
    )

    if result.is_rejected:
        rejection = result.rejection
        assert rejection is not None  # invariante de is_rejected
        return {
            "rejection_reason": rejection,
            "approval_reasons": [],
            "audit_log": [
                AuditEvent(
                    node="evaluate_policy",
                    message=rejection.detail,
                    reason_code=rejection.reason_code,
                )
            ],
        }

    message = (
        f"{len(result.approval_reasons)} motivo(s) de aprobacion (BR-09)."
        if result.approval_reasons
        else "Dentro de politica, sin aprobacion requerida."
    )
    return {
        "rejection_reason": None,
        "approval_reasons": result.approval_reasons,
        "audit_log": [AuditEvent(node="evaluate_policy", message=message)],
    }


async def human_approval(state: QuoteState) -> dict[str, Any]:
    """RF-07: pausa durable en `interrupt()`.

    ADR-003: LangGraph reejecuta este nodo desde el inicio al reanudar, asi
    que debe ser inocuo antes de la pausa -- no hay efectos secundarios
    aqui, solo se arma el payload informativo y se espera la decision."""
    payload = {
        "thread_id": state.thread_id,
        "approval_reasons": [r.model_dump(mode="json") for r in state.approval_reasons],
        "quote": state.quote.model_dump(mode="json") if state.quote is not None else None,
    }
    decision_payload = interrupt(payload)
    decision = HumanDecision.model_validate(decision_payload)
    if decision.decision_id in state.applied_decision_ids:
        # BR-15: un decision_id ya aplicado no reemplaza la decision vigente,
        # aunque llegue con otra accion. `route_after_apply_decision` sigue
        # leyendo la ultima decision aplicada, asi que el caso no avanza.
        return {
            "audit_log": [
                AuditEvent(
                    node="human_approval",
                    message=f"decision_id={decision.decision_id} ya aplicado; se ignora (BR-15).",
                )
            ],
        }
    return {
        "human_decision": decision,
        "audit_log": [
            AuditEvent(
                node="human_approval",
                message=(
                    f"Decision humana recibida: {decision.action.value} "
                    f"(decision_id={decision.decision_id})."
                ),
            )
        ],
    }


async def apply_decision(state: QuoteState) -> dict[str, Any]:
    """BR-14/BR-15/BR-16: aplica la decision humana con idempotencia por
    `decision_id`. Si ya se aplico, no hay efecto adicional -- ni se
    duplica `applied_decision_ids` ni se agrega auditoria de "aplicada" de
    nuevo (BR-15: "no produce efecto adicional y devuelve el estado
    existente"). Este nodo no toca `outcome`: eso es responsabilidad
    exclusiva de `finalize`, y el camino (rechazo / avanzar a borrador /
    volver a pausa por OBSERVE) lo decide `routing.py` (T10)."""
    if state.human_decision is None:
        raise ValueError(
            "apply_decision requiere una decision humana ya registrada por 'human_approval'"
        )

    decision = state.human_decision
    if decision.decision_id in state.applied_decision_ids:
        return {
            "audit_log": [
                AuditEvent(
                    node="apply_decision",
                    message=(
                        f"decision_id={decision.decision_id} ya aplicado; "
                        "sin efecto adicional (BR-15)."
                    ),
                )
            ],
        }

    return {
        "applied_decision_ids": [*state.applied_decision_ids, decision.decision_id],
        "audit_log": [
            AuditEvent(
                node="apply_decision",
                message=(
                    f"Decision {decision.action.value} aplicada por {decision.actor} "
                    f"(decision_id={decision.decision_id})."
                ),
            )
        ],
    }


async def compose_draft(state: QuoteState) -> dict[str, Any]:
    """Redaccion del borrador. En modo test (RF-10) es una plantilla
    determinista, nunca un LLM -- ADR-002 regla 5: "la redaccion no puede
    introducir cifras" que el dominio no haya calculado ya. El borrador
    unicamente reordena valores que ya existen en `state.quote`; un
    extractor real de redaccion (analogo al de LOOP.md) queda fuera del
    alcance de T7-T11."""
    if state.quote is None:
        raise ValueError("compose_draft requiere una cotizacion ya calculada")

    lines_text = "\n".join(
        f"  - {line.quantity} x {line.product_name} ({line.sku}) @ {line.unit_price} c/u"
        for line in state.quote.lines
    )
    draft = (
        f"Cotizacion para {state.customer_id}\n"
        f"{lines_text}\n"
        f"Subtotal: {state.quote.subtotal} {state.quote.currency}\n"
        f"Descuento ({state.quote.discount_pct}%): "
        f"-{state.quote.discount_amount} {state.quote.currency}\n"
        f"Neto: {state.quote.net} {state.quote.currency}\n"
        f"IGV: {state.quote.tax_amount} {state.quote.currency}\n"
        f"Total: {state.quote.total} {state.quote.currency}"
    )
    return {
        "draft": draft,
        "audit_log": [
            AuditEvent(
                node="compose_draft", message="Borrador generado por plantilla determinista."
            )
        ],
    }


async def finalize(state: QuoteState) -> dict[str, Any]:
    """Fija el `Outcome` terminal y el `reason_code` (RF-08), inspeccionando
    lo que los nodos anteriores ya dejaron en el estado -- no decide nada
    nuevo, solo traduce el primer motivo bloqueante en el orden en que el
    grafo pudo haberlo producido."""
    outcome: Outcome
    reason: ReasonCode | None

    if state.extraction is None and state.extraction_error is not None:
        outcome, reason = Outcome.NEEDS_CLARIFICATION, ReasonCode.EXTRACTION_FAILED
    elif state.completeness_error is not None:
        outcome, reason = Outcome.NEEDS_CLARIFICATION, state.completeness_error.reason_code
    elif state.blocking_reason is not None:
        outcome, reason = Outcome.BLOCKED, state.blocking_reason.reason_code
    elif state.rejection_reason is not None:
        outcome, reason = Outcome.REJECTED_BY_POLICY, state.rejection_reason.reason_code
    elif state.human_decision is not None and state.human_decision.action == DecisionAction.REJECT:
        # BR-14: el rechazo humano tambien termina en rechazo. El dominio
        # (T2-T6, contrato fijo) solo define REJECTED_BY_POLICY como estado
        # terminal de rechazo -- no existe un Outcome "REJECTED" separado
        # para el rechazo humano. Se reutiliza REJECTED_BY_POLICY y se
        # conserva el reason_code que origino la aprobacion, para no perder
        # por que el caso llego a revision. Por diseno, se agrupa
        # "rechazado o escalado por politica" en un solo resultado;
        # REQUIREMENTS.md AC-11 corregido para reflejar REJECTED_BY_POLICY.
        outcome = Outcome.REJECTED_BY_POLICY
        reason = state.approval_reasons[0].reason_code if state.approval_reasons else None
    else:
        outcome, reason = Outcome.DRAFT_READY, None

    return {
        "outcome": outcome,
        "reason_code": reason,
        "audit_log": [
            AuditEvent(
                node="finalize",
                message=f"Resultado final: {outcome.value}"
                + (f" / {reason.value}" if reason else "")
                + ".",
                reason_code=reason,
            )
        ],
    }


def _requested_discount_pct(state: QuoteState) -> Decimal:
    """BR-11: sin descuento solicitado en la extraccion, se trata como 0%."""
    if state.extraction is not None and state.extraction.requested_discount_pct is not None:
        return state.extraction.requested_discount_pct
    return Decimal("0")
