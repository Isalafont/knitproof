"""Propriétés du nombre brut de mailles (CLA-65)."""

from decimal import Decimal, localcontext

from hypothesis import example, given
from hypothesis import strategies as st

from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.measure import EXACT, Length, LengthUnit, SwatchMeasurement
from knitproof.engine.cast_on import cast_on, stitches_for_width

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


MULTIPLES = st.integers(min_value=1, max_value=12).flatmap(
    lambda multiple: st.builds(
        StitchMultiple,
        repeat_multiple=st.just(multiple),
        repeat_offset=st.integers(min_value=0, max_value=multiple - 1),
    )
)
LENGTHS_CM = WIDTHS.map(lambda value: Length(value=value, unit=LengthUnit.CM))


def distance(stitches: int, target: Length, swatch: SwatchMeasurement) -> Decimal:
    """Écart exact en produits croisés (même dénominateur pour tous les candidats)."""
    with localcontext(EXACT):
        return abs(stitches * swatch.width.in_cm - target.in_cm * swatch.stitches)


@given(LENGTHS_CM, SWATCHES, MULTIPLES)
@example(
    Length(value=Decimal("43.2"), unit=LengthUnit.CM),
    SwatchMeasurement(
        stitches=Decimal("20"), width=Length(value=Decimal("10"), unit=LengthUnit.CM)
    ),
    StitchMultiple(repeat_multiple=4, repeat_offset=2),
)
def test_cast_on_respects_the_point_and_is_positive(
    target: Length, swatch: SwatchMeasurement, point: StitchMultiple
) -> None:
    result = cast_on(target, swatch, point)

    assert point.accepts(result.stitches)
    assert result.stitches >= 1


@given(LENGTHS_CM, SWATCHES, MULTIPLES)
@example(
    Length(value=Decimal("43.2"), unit=LengthUnit.CM),
    SwatchMeasurement(
        stitches=Decimal("20"), width=Length(value=Decimal("10"), unit=LengthUnit.CM)
    ),
    StitchMultiple(repeat_multiple=4, repeat_offset=2),
)
def test_no_candidate_is_closer_and_ties_go_down(
    target: Length, swatch: SwatchMeasurement, point: StitchMultiple
) -> None:
    result = cast_on(target, swatch, point)
    chosen = distance(result.stitches, target, swatch)

    for step in (-2, -1, 1, 2):
        other = result.stitches + step * point.repeat_multiple
        if other < 1:
            continue
        other_distance = distance(other, target, swatch)
        assert chosen <= other_distance
        if other_distance == chosen:
            assert result.stitches < other


@given(LENGTHS_CM, LENGTHS_CM, SWATCHES, MULTIPLES)
def test_cast_on_never_decreases_with_width(
    first: Length, second: Length, swatch: SwatchMeasurement, point: StitchMultiple
) -> None:
    small, large = sorted((first, second), key=lambda length: length.value)

    assert cast_on(small, swatch, point).stitches <= cast_on(large, swatch, point).stitches
