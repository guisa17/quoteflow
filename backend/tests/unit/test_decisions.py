"""BR-15/BR-19 -- clasificacion de una decision humana entrante."""

from datetime import UTC, datetime

import pytest

from app.domain.decisions import DecisionVerdict, classify_decision
from app.domain.enums import DecisionAction
from app.domain.models import HumanDecision


def _decision(decision_id: str, action: DecisionAction) -> HumanDecision:
    return HumanDecision(
        decision_id=decision_id,
        action=action,
        actor="jefe.ventas",
        timestamp=datetime.now(UTC),
    )


def test_new_decision_on_paused_case_is_applied() -> None:
    verdict = classify_decision(
        decision_id="dec-1",
        action=DecisionAction.APPROVE,
        paused=True,
        applied_decision_ids=[],
        last_decision=None,
    )
    assert verdict == DecisionVerdict.APPLY


@pytest.mark.parametrize("paused", [True, False])
def test_br15_exact_replay_of_the_last_decision_is_a_replay(paused: bool) -> None:
    action = DecisionAction.OBSERVE if paused else DecisionAction.APPROVE
    verdict = classify_decision(
        decision_id="dec-1",
        action=action,
        paused=paused,
        applied_decision_ids=["dec-1"],
        last_decision=_decision("dec-1", action),
    )
    assert verdict == DecisionVerdict.REPLAY


def test_br15_replay_of_an_earlier_observation_is_a_replay() -> None:
    """Un decision_id aplicado que ya no es el ultimo solo pudo ser OBSERVE:
    es la unica accion que deja el caso abierto para otra decision."""
    verdict = classify_decision(
        decision_id="dec-observe",
        action=DecisionAction.OBSERVE,
        paused=False,
        applied_decision_ids=["dec-observe", "dec-approve"],
        last_decision=_decision("dec-approve", DecisionAction.APPROVE),
    )
    assert verdict == DecisionVerdict.REPLAY


def test_br19_same_decision_id_with_another_action_is_a_conflict() -> None:
    verdict = classify_decision(
        decision_id="dec-1",
        action=DecisionAction.APPROVE,
        paused=True,
        applied_decision_ids=["dec-1"],
        last_decision=_decision("dec-1", DecisionAction.OBSERVE),
    )
    assert verdict == DecisionVerdict.CONFLICT


def test_br19_new_decision_on_a_closed_case_is_a_conflict() -> None:
    verdict = classify_decision(
        decision_id="dec-2",
        action=DecisionAction.REJECT,
        paused=False,
        applied_decision_ids=["dec-1"],
        last_decision=_decision("dec-1", DecisionAction.APPROVE),
    )
    assert verdict == DecisionVerdict.CONFLICT


def test_br19_decision_on_a_case_that_never_needed_approval_is_a_conflict() -> None:
    verdict = classify_decision(
        decision_id="dec-1",
        action=DecisionAction.APPROVE,
        paused=False,
        applied_decision_ids=[],
        last_decision=None,
    )
    assert verdict == DecisionVerdict.CONFLICT
