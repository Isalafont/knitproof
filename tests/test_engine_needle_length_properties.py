"""Le produit croisé de la longueur d’aiguille s’accorde avec le quotient (CLA-68)."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.measure import DIVISION, Length, LengthUnit, SwatchMeasurement
from knitproof.engine.needle_length import _too_long


@given(
    length=st.integers(min_value=10, max_value=150),
    stitches=st.integers(min_value=8, max_value=400),
    gauge=st.integers(min_value=10, max_value=40),
)
def test_the_cross_product_agrees_with_the_quotient(length: int, stitches: int, gauge: int) -> None:
    swatch = SwatchMeasurement(
        stitches=Decimal(gauge), width=Length(value=Decimal(10), unit=LengthUnit.CM)
    )
    circumference = DIVISION.divide(Decimal(stitches) * 10, Decimal(gauge))

    assert _too_long(Decimal(length), stitches, swatch) == (Decimal(length) > circumference)
