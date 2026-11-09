"""Estado tipado del grafo (T7, PROJECT.md §4.2).

`QuoteState` es el estado explicito del flujo: cada nodo del
grafo (T9) lee un subconjunto de estos campos y devuelve solo los que
actualiza -- nunca variables sueltas fuera del estado. LangGraph fusiona esas
actualizaciones parciales campo a campo y persiste el resultado en el
checkpointer (T11).

Este archivo vive en `app/graph/`, no en `app/domain/` (CLAUDE.md §2): orquesta
la forma del estado, no decide nada. Los tipos que agrega (`Extraction`,
`ResolvedLine`, `Quote`, `ApprovalReason`, `HumanDecision`) son del dominio y
se importan tal cual -- este modulo no los reinterpreta ni les agrega logica.

`None` en un campo significa "todavia no se produjo" (el nodo que lo llena
no se ha ejecutado o no aplica en esta ruta), nunca "vacio por error".
"""

import operator
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.domain.enums import Outcome, ReasonCode, Tier
from app.domain.models import (
    ApprovalReason,
    Customer,
    Extraction,
    HumanDecision,
    Quote,
    ResolvedLine,
)


class AuditEvent(BaseModel):
    """RF-08: un evento legible de la traza de ejecucion.

    Cada nodo agrega los suyos; `audit_log` se acumula (no se reemplaza) a
    traves de toda la ejecucion via el reducer `operator.add` de abajo.
    """

    node: str
    message: str
    reason_code: ReasonCode | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QuoteState(BaseModel):
    """Estado completo de una solicitud a lo largo del grafo.

    Agrupado por el nodo que produce cada campo (PROJECT.md §4.2), en el
    mismo orden en que el grafo los recorre.
    """

    # --- ingest: normaliza la solicitud, abre thread_id ---
    thread_id: str
    customer_id: str
    raw_text: str

    # --- extract: salida estructurada del LLM (RF-05) ---
    extraction: Extraction | None = None
    extraction_attempts: int = 0
    extraction_error: str | None = None

    # --- resolve_customer: cliente + tier (BR-08) ---
    customer: Customer | None = None
    customer_is_known: bool | None = None
    tier: Tier | None = None

    # --- validate_request: completitud (BR-10, BR-11) ---
    completeness_error: ApprovalReason | None = None

    # --- resolve_catalog / check_inventory: lineas resueltas (BR-02, BR-12, BR-13) ---
    resolved_lines: list[ResolvedLine] = []
    blocking_reason: ApprovalReason | None = None

    # --- price_quote: cotizacion calculada (RF-06) ---
    quote: Quote | None = None

    # --- evaluate_policy: BR-05..BR-09 ---
    rejection_reason: ApprovalReason | None = None
    approval_reasons: list[ApprovalReason] = []

    # --- human_approval / apply_decision: BR-14..BR-16 ---
    human_decision: HumanDecision | None = None
    applied_decision_ids: list[str] = []

    # --- compose_draft ---
    draft: str | None = None

    # --- finalize: resultado terminal ---
    outcome: Outcome | None = None
    reason_code: ReasonCode | None = None

    # --- auditoria acumulativa (RF-08), todos los nodos escriben aqui ---
    audit_log: Annotated[list[AuditEvent], operator.add] = []
