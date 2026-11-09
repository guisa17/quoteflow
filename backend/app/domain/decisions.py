"""Clasificacion de una decision humana entrante (BR-15, BR-19).

Funcion pura: la API la consulta antes de reanudar el grafo. Vive en el dominio
porque decidir si una decision es nueva, un reenvio o un conflicto es una regla
de negocio, no serializacion (CLAUDE.md §2).
"""

from collections.abc import Sequence
from enum import StrEnum

from app.domain.enums import DecisionAction
from app.domain.models import HumanDecision


class DecisionVerdict(StrEnum):
    APPLY = "APPLY"
    REPLAY = "REPLAY"
    CONFLICT = "CONFLICT"


def classify_decision(
    *,
    decision_id: str,
    action: DecisionAction,
    paused: bool,
    applied_decision_ids: Sequence[str],
    last_decision: HumanDecision | None,
) -> DecisionVerdict:
    """BR-15: reenviar la misma decision no tiene efecto. BR-19: una decision
    que contradice lo ya registrado se reporta, nunca se descarta en silencio."""
    if decision_id in applied_decision_ids:
        # Si no es la ultima, solo pudo ser OBSERVE: es la unica accion que deja
        # el caso abierto para recibir otra decision (BR-14).
        prior_action = (
            last_decision.action
            if last_decision is not None and last_decision.decision_id == decision_id
            else DecisionAction.OBSERVE
        )
        return DecisionVerdict.REPLAY if prior_action == action else DecisionVerdict.CONFLICT

    return DecisionVerdict.APPLY if paused else DecisionVerdict.CONFLICT
