"""`StitchPattern` : un point et son multiple (CLA-67, ADR 0019 §6)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.stitch import StitchPattern


def test_a_stitch_pattern_carries_its_multiple() -> None:
    pattern = StitchPattern(
        id="cotes-2-2",
        names=("côtes 2/2",),
        multiple=StitchMultiple(repeat_multiple=4, repeat_offset=0),
    )

    assert pattern.multiple.accepts(88)
    assert not pattern.multiple.accepts(90)


def test_a_remainder_at_or_above_the_multiple_is_refused() -> None:
    with pytest.raises(ValidationError):
        StitchPattern.model_validate(
            {"id": "x", "names": [], "multiple": {"repeat_multiple": 4, "repeat_offset": 4}}
        )


def test_a_stitch_pattern_refuses_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        StitchPattern.model_validate(
            {
                "id": "x",
                "names": [],
                "multiple": {"repeat_multiple": 1, "repeat_offset": 0},
                "points": [],
            }
        )
