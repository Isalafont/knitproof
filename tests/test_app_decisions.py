"""`Decisions` : le registre des décisions, consommées par l’étape de leur question (CLA-206)."""

import datetime

import pytest

from knitproof.app.decisions import DecisionError, Decisions
from knitproof.domain.decision import Decision
from knitproof.domain.question import PendingQuestion

QUESTION = PendingQuestion(code="gauge_blocking_unknown", text="Q ?", options=("a", "b"))


def _decision(code: str = "gauge_blocking_unknown", choice: str = "a") -> Decision:
    return Decision(question=code, choice=choice, decided_on=datetime.date(2026, 11, 23))


def test_answer_gives_the_decision_of_the_same_code_and_consumes_it() -> None:
    decision = _decision()
    decisions = Decisions((decision,))

    assert decisions.answer(QUESTION) == decision
    assert decisions.consumed == (decision,)
    decisions.check_all_consumed()


def test_a_question_without_decision_gives_none() -> None:
    decisions = Decisions((_decision("other"),))

    assert decisions.answer(QUESTION) is None
    assert decisions.consumed == ()


def test_an_unknown_option_names_the_question_and_the_expected_options() -> None:
    decisions = Decisions((_decision(choice="c"),))

    with pytest.raises(DecisionError, match="gauge_blocking_unknown") as error:
        decisions.answer(QUESTION)

    assert "a, b" in str(error.value)


def test_a_decision_never_consumed_names_its_code() -> None:
    decisions = Decisions((_decision("crown_odd_stitches"),))

    with pytest.raises(DecisionError, match="crown_odd_stitches"):
        decisions.check_all_consumed()


def test_two_decisions_on_the_same_question_are_refused() -> None:
    with pytest.raises(DecisionError, match="gauge_blocking_unknown"):
        Decisions((_decision(), _decision(choice="b")))


def test_a_decision_on_a_question_that_cannot_be_answered_says_so() -> None:
    decisions = Decisions((_decision("crown_odd_stitches"),))

    with pytest.raises(DecisionError, match="cette question ne se répond pas par une décision"):
        decisions.check_all_consumed()
