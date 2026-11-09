"""Validateurs de `CrownRule` (CLA-67, ADR 0019)."""

import datetime

import pytest
from pydantic import ValidationError

from knitproof.domain.construction import CrownRule

ENTRY = {
    "id": "calotte",
    "source": {
        "kind": "person_decision",
        "reference": "Isabelle, ADR 0019",
        "read_on": datetime.date(2026, 11, 2),
    },
    "decreases_per_round": 8,
    "last_round_below": 24,
    "min_cast_on": 32,
    "every_round_last": 3,
}


def test_the_last_round_threshold_cannot_exceed_the_minimum_cast_on() -> None:
    with pytest.raises(ValidationError, match="last_round_below"):
        CrownRule.model_validate({**ENTRY, "last_round_below": 33})


def test_a_threshold_equal_to_the_minimum_cast_on_is_accepted() -> None:
    assert CrownRule.model_validate({**ENTRY, "last_round_below": 32}).min_cast_on == 32
