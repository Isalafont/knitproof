"""Nombre brut de mailles pour une largeur (CLA-65)."""

from decimal import Decimal

import pytest

from knitproof.domain.measure import DIVISION, Length, LengthUnit, SwatchMeasurement
from knitproof.engine.cast_on import stitches_for_width


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
