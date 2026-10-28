"""Comparaison des aiguilles de l’échantillon et du projet (CLA-104)."""

from decimal import Decimal

import pytest

from knitproof.domain.needle import (
    Needle,
    NeedleKind,
    NeedleMismatch,
    NeedleSize,
    NeedleSystem,
)
from knitproof.engine.needle import check_needles


def needle(system: NeedleSystem, original: str, mm: str | None = None) -> Needle:
    size = NeedleSize(system=system, original=original, mm=None if mm is None else Decimal(mm))
    return Needle(size=size, kind=NeedleKind.STRAIGHT)


def reasons(swatch: Needle, project: Needle) -> tuple[NeedleMismatch, ...]:
    forward = check_needles(swatch, project).reasons
    assert check_needles(project, swatch).reasons == forward
    return forward


def test_same_mm_written_differently_has_no_reason() -> None:
    assert reasons(needle(NeedleSystem.MM, "4 mm"), needle(NeedleSystem.MM, "4,0 mm")) == ()


def test_4_mm_against_4_5_mm_differs() -> None:
    result = reasons(needle(NeedleSystem.MM, "4 mm"), needle(NeedleSystem.MM, "4.5mm"))
    assert result == (NeedleMismatch.SIZE_DIFFERS,)


def test_us_6_with_mm_against_4_mm_has_no_reason() -> None:
    assert reasons(needle(NeedleSystem.US, "US 6", "4"), needle(NeedleSystem.MM, "4 mm")) == ()


def test_us_6_against_4_mm_is_not_comparable() -> None:
    result = reasons(needle(NeedleSystem.US, "US 6"), needle(NeedleSystem.MM, "4 mm"))
    assert result == (NeedleMismatch.SIZES_NOT_COMPARABLE,)


def test_us_6_against_jp_6_is_not_comparable() -> None:
    result = reasons(needle(NeedleSystem.US, "US 6"), needle(NeedleSystem.JP, "6号"))
    assert result == (NeedleMismatch.SIZES_NOT_COMPARABLE,)


def test_us_6_against_uk_8_is_not_comparable() -> None:
    result = reasons(needle(NeedleSystem.US, "US 6"), needle(NeedleSystem.UK, "UK 8"))
    assert result == (NeedleMismatch.SIZES_NOT_COMPARABLE,)


def test_same_text_in_the_same_system_has_no_reason() -> None:
    assert reasons(needle(NeedleSystem.US, "US 6"), needle(NeedleSystem.US, "6")) == ()


@pytest.mark.parametrize(("a", "b"), [("US 00", "US 0"), ("US 000", "US 0")])
def test_us_zero_sizes_stay_distinct(a: str, b: str) -> None:
    result = reasons(needle(NeedleSystem.US, a), needle(NeedleSystem.US, b))
    assert result == (NeedleMismatch.SIZE_DIFFERS,)


def test_entered_mm_take_precedence_when_they_differ() -> None:
    result = reasons(needle(NeedleSystem.US, "US 6", "4"), needle(NeedleSystem.US, "US 6", "3.75"))
    assert result == (NeedleMismatch.SIZE_DIFFERS,)


def test_entered_mm_take_precedence_in_the_same_system() -> None:
    assert reasons(needle(NeedleSystem.US, "US 6", "4"), needle(NeedleSystem.US, "US 7", "4")) == ()


def test_10_mm_against_10_00_has_no_reason() -> None:
    assert reasons(needle(NeedleSystem.MM, "10 mm"), needle(NeedleSystem.MM, "10.00")) == ()


@pytest.mark.parametrize(("a", "b"), [("3,25 mm", "3,5 mm"), ("3,75 mm", "4 mm")])
def test_mm_sizes_are_compared_without_rounding(a: str, b: str) -> None:
    result = reasons(needle(NeedleSystem.MM, a), needle(NeedleSystem.MM, b))
    assert result == (NeedleMismatch.SIZE_DIFFERS,)


def test_3_50mm_against_3_5_mm_has_no_reason() -> None:
    assert reasons(needle(NeedleSystem.MM, "3.50mm"), needle(NeedleSystem.MM, "3,5 mm")) == ()


def test_a_needle_against_itself_has_no_reason() -> None:
    a = needle(NeedleSystem.US, "US 6")
    assert check_needles(a, a).matches
