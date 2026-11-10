"""Point déclaré et résultat du montage (CLA-65)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.cast_on import CastOnResult, RoundingRule, StitchMultiple
from knitproof.domain.measure import Length, LengthUnit


def test_a_stitch_multiple_accepts_its_numbers() -> None:
    point = StitchMultiple(repeat_multiple=4, repeat_offset=2)

    assert [point.accepts(n) for n in (86, 88, 90, 2)] == [True, False, True, True]


def test_a_stitch_multiple_with_no_offset() -> None:
    point = StitchMultiple(repeat_multiple=4, repeat_offset=0)

    assert [point.accepts(n) for n in (88, 90)] == [True, False]


@pytest.mark.parametrize(
    "raw",
    [
        {"repeat_multiple": 0, "repeat_offset": 0},
        {"repeat_multiple": 4, "repeat_offset": -1},
        {"repeat_multiple": 4, "repeat_offset": 4},
        {"repeat_multiple": 4, "repeat_offset": 0, "names": ["côtes"]},
    ],
)
def test_an_invalid_stitch_multiple_is_rejected(raw: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        StitchMultiple.model_validate(raw)


def test_a_cast_on_result_traces_its_rule() -> None:
    result = CastOnResult(
        target=Length(value=Decimal("43.2"), unit=LengthUnit.CM),
        raw_stitches=Decimal("86.4"),
        stitches=88,
        rounding_rule=RoundingRule.NEAREST_TIE_DOWN,
        finished_cm=Decimal("44"),
    )

    assert result.rounding_rule == "nearest_tie_down"
