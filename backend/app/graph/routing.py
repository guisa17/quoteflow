"""Routing condicional del grafo (T10, PROJECT.md §2.2 paso 4 / ADR-002 §4.2.2).

Cada funcion de este modulo es una arista condicional de LangGraph: recibe
el `QuoteState` ya actualizado por el nodo anterior (T9) y devuelve el
nombre del siguiente nodo. Ninguna decide una regla nueva -- solo traduce lo
que los nodos ya dejaron en el estado (`blocking_reason`, `rejection_reason`,
`approval_reasons`, `human_decision`) a un salto en el grafo. La regla en si
(BR-xx) ya se aplico antes, en `app/domain/` o en el nodo correspondiente.

Los seis casos de enrutamiento de PROJECT.md §2.2 paso 4 -- "completo /
aclaracion / SKU desconocido / sin stock / sujeto a aprobacion / rechazo" --
mas el fallo recuperable de la extraccion (RF-05, ADR-002 §4.2.2), se
resuelven en los seis puntos de decision de abajo:

| Punto de decision              | Caso(s) que resuelve                        |
|---------------------------------|----------------------------------------------|
| `route_after_extract`           | fallo recuperable (RF-05)                    |
| `route_after_validate_request`  | aclaracion (BR-10/11)                        |
| `route_after_resolve_catalog`   | SKU desconocido (BR-02/BR-12)                |
| `route_after_check_inventory`   | sin stock (BR-13)                            |
| `route_after_evaluate_policy`   | rechazo, sujeto a aprobacion, completo       |
| `route_after_apply_decision`    | BR-14: APPROVE / REJECT / OBSERVE            |
"""

from app.domain.enums import DecisionAction
from app.graph.state import QuoteState

MAX_EXTRACTION_ATTEMPTS = 2  # RF-05: un intento inicial + un reintento, no mas.

# Nombres de nodo -- deben coincidir con los registrados en app/graph/build.py (T11).
INGEST = "ingest"
EXTRACT = "extract"
RESOLVE_CUSTOMER = "resolve_customer"
VALIDATE_REQUEST = "validate_request"
RESOLVE_CATALOG = "resolve_catalog"
CHECK_INVENTORY = "check_inventory"
PRICE_QUOTE = "price_quote"
EVALUATE_POLICY = "evaluate_policy"
HUMAN_APPROVAL = "human_approval"
APPLY_DECISION = "apply_decision"
COMPOSE_DRAFT = "compose_draft"
FINALIZE = "finalize"


def route_after_extract(state: QuoteState) -> str:
    """RF-05, fallo recuperable: si la extraccion fallo y quedan reintentos
    (`MAX_EXTRACTION_ATTEMPTS`), se reintenta -- vuelve al propio nodo
    `extract`. Si se agotaron, se degrada a `NEEDS_CLARIFICATION` /
    `EXTRACTION_FAILED` via `finalize`. El sistema nunca cotiza sobre una
    extraccion no validada (PROJECT.md §4.2.2)."""
    if state.extraction is not None:
        return RESOLVE_CUSTOMER
    if state.extraction_attempts < MAX_EXTRACTION_ATTEMPTS:
        return EXTRACT
    return FINALIZE


def route_after_validate_request(state: QuoteState) -> str:
    """Caso "aclaracion" (BR-10/11): informacion esencial faltante corta el
    flujo antes de tocar catalogo o inventario -- ni siquiera se intenta
    resolver un SKU si no hay cantidad valida."""
    if state.completeness_error is not None:
        return FINALIZE
    return RESOLVE_CATALOG


def route_after_resolve_catalog(state: QuoteState) -> str:
    """Caso "SKU desconocido" (BR-02/BR-12): sin sustitucion por similitud."""
    if state.blocking_reason is not None:
        return FINALIZE
    return CHECK_INVENTORY


def route_after_check_inventory(state: QuoteState) -> str:
    """Caso "sin stock" (BR-13): disponible < solicitado detiene la
    solicitud completa, no solo la linea afectada (BR-12)."""
    if state.blocking_reason is not None:
        return FINALIZE
    return PRICE_QUOTE


def route_after_evaluate_policy(state: QuoteState) -> str:
    """Casos "rechazo" (BR-07/BR-09), "sujeto a aprobacion" (BR-05/BR-06/BR-08)
    y "completo": el rechazo por techo duro se verifica primero porque BR-09
    dice que domina sobre cualquier motivo de aprobacion concurrente -- el
    propio `evaluate_policy` (T9) ya garantiza que `approval_reasons` viene
    vacio cuando hay rechazo, asi que el orden aqui es solo defensivo."""
    if state.rejection_reason is not None:
        return FINALIZE
    if state.approval_reasons:
        return HUMAN_APPROVAL
    return COMPOSE_DRAFT


def route_after_apply_decision(state: QuoteState) -> str:
    """BR-14: `APPROVE` avanza a redactar el borrador; `REJECT` termina en
    rechazo; `OBSERVE` ("observacion sin resolver, mantiene el caso en
    pausa") vuelve a `human_approval`, no a `finalize` -- el caso sigue
    abierto hasta una decision que sí lo resuelva."""
    if state.human_decision is None:
        raise ValueError("route_after_apply_decision requiere una decision humana ya aplicada")

    action = state.human_decision.action
    if action == DecisionAction.APPROVE:
        return COMPOSE_DRAFT
    if action == DecisionAction.REJECT:
        return FINALIZE
    return HUMAN_APPROVAL  # BR-14: OBSERVE
