"""Nombre brut de mailles pour une largeur (CLA-65)."""

from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from knitproof.domain.cast_on import CastOnRejection, RoundingRule, StitchMultiple
from knitproof.domain.measure import DIVISION, EXACT, Length, LengthUnit, SwatchMeasurement
from knitproof.engine.cast_on import cast_on, check_cast_on, stitches_for_width


def length(value: str, unit: LengthUnit = LengthUnit.CM) -> Length:
    return Length(value=Decimal(value), unit=unit)


def swatch(stitches: str, width: Length) -> SwatchMeasurement:
    return SwatchMeasurement(stitches=Decimal(stitches), width=width)


def test_raw_stitches_of_the_readme_example() -> None:
    assert stitches_for_width(length("43.2"), swatch("20", length("10"))) == Decimal("86.4")


def test_raw_stitches_with_a_swatch_in_inches() -> None:
    swatch_in = swatch("22", length("4", LengthUnit.IN))

    assert stitches_for_width(length("17", LengthUnit.IN), swatch_in) == Decimal("93.5")


def test_division_refuses_a_float() -> None:
    # L’ADR 0015 justifie DIVISION.divide à la place de `/` par ce refus.
    with pytest.raises(TypeError):
        DIVISION.divide(Decimal("1"), 1.5)  # type: ignore[arg-type]


def test_floor_division_under_exact_signals_nothing() -> None:
    # La doc ne dit pas si `//` signale Inexact ou Rounded quand il tronque.
    with localcontext(EXACT):
        assert Decimal("7") // Decimal("2") == Decimal("3")
        assert Decimal("-7") // Decimal("2") == Decimal("-3")


@pytest.mark.parametrize(
    ("width", "swatch_", "point", "raw", "expected", "finished"),
    [
        ("43.2", swatch("20", length("10")), (4, 0), "86.4", 88, "44"),
        ("43", swatch("20", length("10")), (4, 0), "86", 84, "42"),
        ("43.2", swatch("20", length("10")), (4, 2), "86.4", 86, "43"),
        ("0.1", swatch("20", length("10")), (4, 0), "0.2", 4, "2"),
        ("0.1", swatch("20", length("10")), (4, 2), "0.2", 2, "1"),
        ("40", swatch("22.5", length("10")), (6, 0), "90", 90, "40"),
    ],
)
def test_cast_on_examples(
    width: str,
    swatch_: SwatchMeasurement,
    point: tuple[int, int],
    raw: str,
    expected: int,
    finished: str,
) -> None:
    stitch = StitchMultiple(repeat_multiple=point[0], repeat_offset=point[1])

    result = cast_on(length(width), swatch_, stitch)

    assert (result.raw_stitches, result.stitches, result.finished_cm) == (
        Decimal(raw),
        expected,
        Decimal(finished),
    )
    assert result.target == length(width)
    assert result.rounding_rule is RoundingRule.NEAREST_TIE_DOWN


def test_cast_on_in_inches() -> None:
    swatch_in = swatch("22", length("4", LengthUnit.IN))
    stitch = StitchMultiple(repeat_multiple=4, repeat_offset=0)

    result = cast_on(length("17", LengthUnit.IN), swatch_in, stitch)

    assert (result.raw_stitches, result.stitches) == (Decimal("93.5"), 92)
    assert result.target.unit is LengthUnit.IN
    assert str(result.finished_cm).startswith("42.4872")


TARGET = length("43.2")
SWATCH = swatch("20", length("10"))
POINT = StitchMultiple(repeat_multiple=4, repeat_offset=0)


def test_a_proposal_that_differs_from_the_calculation_is_rejected() -> None:
    check = check_cast_on(120, TARGET, SWATCH, POINT)

    assert check.reasons == (CastOnRejection.DIFFERS_FROM_CALCULATION,)
    assert (check.expected, check.proposed_finished_cm) == (88, Decimal("60"))
    assert not check.accepted


def test_a_proposal_with_both_defects_gives_both_reasons() -> None:
    check = check_cast_on(90, TARGET, SWATCH, POINT)

    assert check.reasons == (
        CastOnRejection.STITCH_MULTIPLE_NOT_RESPECTED,
        CastOnRejection.DIFFERS_FROM_CALCULATION,
    )
    assert check.proposed_finished_cm == Decimal("45")


def test_the_calculated_cast_on_is_accepted() -> None:
    check = check_cast_on(88, TARGET, SWATCH, POINT)

    assert (check.reasons, check.proposed_finished_cm, check.accepted) == ((), Decimal("44"), True)


def test_a_proposal_of_zero_is_rejected_by_validation() -> None:
    with pytest.raises(ValidationError):
        check_cast_on(0, TARGET, SWATCH, POINT)
