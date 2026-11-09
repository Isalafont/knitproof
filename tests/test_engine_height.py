"""Rangs d’une hauteur et rangs tricotés (CLA-68, ADR 0028)."""

from decimal import Decimal

import pytest

from knitproof.domain.beanie import RowRounding
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.engine.height import knitted_rows, rounds_for_height


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def swatch(rows: str = "30", height: str = "10") -> SwatchMeasurement:
    return SwatchMeasurement(
        stitches=Decimal("20"), width=cm("10"), rows=Decimal(rows), height=cm(height)
    )


def test_25_cm_at_30_rows_per_10_cm_is_75_rows() -> None:
    count = rounds_for_height(cm("25"), swatch())

    assert count.rows == 75
    assert count.raw == Decimal("75")
    assert count.rule is RowRounding.NEAREST_TIE_DOWN


def test_a_tie_rounds_down() -> None:
    # 2,5 cm à 30 rangs pour 10 cm : 7,5 rangs.
    assert rounds_for_height(cm("2.5"), swatch()).rows == 7


def test_just_above_a_tie_rounds_up() -> None:
    assert rounds_for_height(cm("2.51"), swatch()).rows == 8


def test_a_height_in_inches_is_converted() -> None:
    assert rounds_for_height(Length(value=Decimal("10"), unit=LengthUnit.IN), swatch()).rows == 76


def test_a_swatch_without_rows_is_refused() -> None:
    bare = SwatchMeasurement(stitches=Decimal("20"), width=cm("10"))

    with pytest.raises(ValueError, match="rangs"):
        rounds_for_height(cm("25"), bare)


def test_a_folded_brim_counts_twice_in_the_knitted_rows() -> None:
    rows = knitted_rows(cm("20"), cm("5"), folded=True, swatch=swatch())

    assert rows.total.rows == 75
    assert rows.brim.rows == 30


def test_a_flat_brim_is_its_own_height() -> None:
    rows = knitted_rows(cm("20"), cm("5"), folded=False, swatch=swatch())

    assert rows.total.rows == 60
    assert rows.brim.rows == 15
