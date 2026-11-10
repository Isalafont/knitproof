"""Propriétés des rangs d’une hauteur (CLA-68)."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.engine.height import rounds_for_height

HEIGHTS = st.decimals(
    min_value=Decimal("0.1"), max_value=Decimal("99.9"), places=1, allow_nan=False
)
SWATCH = SwatchMeasurement(
    stitches=Decimal("20"),
    width=Length(value=Decimal("10"), unit=LengthUnit.CM),
    rows=Decimal("30"),
    height=Length(value=Decimal("10"), unit=LengthUnit.CM),
)


def cm(value: Decimal) -> Length:
    return Length(value=value, unit=LengthUnit.CM)


@given(low=HEIGHTS, high=HEIGHTS)
def test_rows_never_decrease_when_the_height_grows(low: Decimal, high: Decimal) -> None:
    low, high = min(low, high), max(low, high)

    assert rounds_for_height(cm(low), SWATCH).rows <= rounds_for_height(cm(high), SWATCH).rows


@given(height=st.decimals(min_value=Decimal("0.5"), max_value=Decimal("99.9"), places=1))
def test_the_rounded_rows_stay_within_half_a_row_of_the_raw_count(height: Decimal) -> None:
    count = rounds_for_height(cm(height), SWATCH)

    assert abs(Decimal(count.rows) - count.raw) <= Decimal("0.5")
