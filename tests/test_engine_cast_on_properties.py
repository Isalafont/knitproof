"""Propriétés du nombre brut de mailles (CLA-65)."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.engine.cast_on import stitches_for_width

WIDTHS = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("99.99"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
SWATCHES = st.builds(
    SwatchMeasurement,
    stitches=st.decimals(
        min_value=Decimal("1"),
        max_value=Decimal("99.9"),
        places=1,
        allow_nan=False,
        allow_infinity=False,
    ),
    width=st.builds(
        Length,
        value=st.decimals(
            min_value=Decimal("1"),
            max_value=Decimal("99.9"),
            places=1,
            allow_nan=False,
            allow_infinity=False,
        ),
        unit=st.sampled_from(LengthUnit),
    ),
)


@given(WIDTHS, WIDTHS, SWATCHES)
def test_raw_stitches_never_decrease_with_width(
    first: Decimal, second: Decimal, swatch: SwatchMeasurement
) -> None:
    small, large = sorted((first, second))

    assert stitches_for_width(
        Length(value=small, unit=LengthUnit.CM), swatch
    ) <= stitches_for_width(Length(value=large, unit=LengthUnit.CM), swatch)


@given(st.integers(min_value=1, max_value=99), SWATCHES)
def test_the_unit_of_the_width_changes_nothing(inches: int, swatch: SwatchMeasurement) -> None:
    in_inches = Length(value=Decimal(inches), unit=LengthUnit.IN)
    in_cm = Length(value=Decimal(inches) * Decimal("2.54"), unit=LengthUnit.CM)

    assert stitches_for_width(in_inches, swatch) == stitches_for_width(in_cm, swatch)
