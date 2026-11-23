"""`Decision` : le choix d’une personne devant une question en attente (CLA-206)."""

import datetime

import pytest
from pydantic import ValidationError

from knitproof.domain.decision import Decision

DECIDED_ON = datetime.date(2026, 11, 23)


def _data(**changes: object) -> dict[str, object]:
    return {
        "question": "gauge_blocking_unknown",
        "choice": "après lavage",
        "decided_on": DECIDED_ON,
        **changes,
    }


def test_a_decision_keeps_its_fields() -> None:
    decision = Decision.model_validate(_data(reason="mesuré après un lavage"))

    assert decision.question == "gauge_blocking_unknown"
    assert decision.choice == "après lavage"
    assert decision.decided_on == DECIDED_ON
    assert decision.reason == "mesuré après un lavage"


def test_the_reason_is_optional() -> None:
    assert Decision.model_validate(_data()).reason is None


def test_the_date_is_required() -> None:
    data = _data()
    del data["decided_on"]

    with pytest.raises(ValidationError, match="decided_on"):
        Decision.model_validate(data)


@pytest.mark.parametrize("decided_on", ["2026-11-23", datetime.datetime(2026, 11, 23, 10, 0)])
def test_only_a_date_is_accepted(decided_on: object) -> None:
    with pytest.raises(ValidationError, match="une date AAAA-MM-JJ est attendue"):
        Decision.model_validate(_data(decided_on=decided_on))


@pytest.mark.parametrize("field", ["question", "choice"])
@pytest.mark.parametrize("value", ["", "   "])
def test_an_empty_question_or_choice_is_refused(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match=field):
        Decision.model_validate(_data(**{field: value}))


def test_an_extra_key_is_refused() -> None:
    with pytest.raises(ValidationError, match="extra"):
        Decision.model_validate(_data(extra="x"))


def test_a_decision_is_frozen() -> None:
    decision = Decision.model_validate(_data())

    with pytest.raises(ValidationError, match="frozen"):
        decision.choice = "avant lavage"  # type: ignore[misc]
