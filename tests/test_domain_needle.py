"""Aiguilles dans leur système d’origine, sans table de correspondance (CLA-104)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.needle import NeedleSize, NeedleSystem


def size(system: NeedleSystem, original: str, mm: Decimal | None = None) -> NeedleSize:
    return NeedleSize(system=system, original=original, mm=mm)


@pytest.mark.parametrize("original", ["3.50mm", "3,5 mm", "3.5 mm", "3.5MM"])
def test_mm_sizes_written_differently_are_the_same_size(original: str) -> None:
    assert size(NeedleSystem.MM, original).known_mm == Decimal("3.5")


def test_mm_normalized_drops_trailing_zeros_without_exponent() -> None:
    assert size(NeedleSystem.MM, "10.00").normalized == "10"


@pytest.mark.parametrize(
    ("system", "original", "normalized"),
    [
        (NeedleSystem.US, "US 6", "6"),
        (NeedleSystem.US, "us6", "6"),
        (NeedleSystem.US, "6", "6"),
        (NeedleSystem.US, "US 10½", "10½"),
        (NeedleSystem.US, "US 00", "00"),
        (NeedleSystem.US, "US 000", "000"),
        (NeedleSystem.US, "US 0000000", "0000000"),
        (NeedleSystem.UK, "UK 8", "8"),
        (NeedleSystem.UK, "000", "000"),
        (NeedleSystem.JP, "6号", "6"),
        (NeedleSystem.JP, "JP 6", "6"),
        (NeedleSystem.JP, "6", "6"),
        (NeedleSystem.US, "US 37", "37"),
        (NeedleSystem.JP, "42", "42"),
        (NeedleSystem.MM, "3,3 mm", "3.3"),
    ],
)
def test_a_size_is_normalized_inside_its_own_system(
    system: NeedleSystem, original: str, normalized: str
) -> None:
    assert size(system, original).normalized == normalized


def test_original_notation_is_kept() -> None:
    assert size(NeedleSystem.US, "US 6").original == "US 6"


def test_us_double_zero_differs_from_zero() -> None:
    assert size(NeedleSystem.US, "US 00").normalized != size(NeedleSystem.US, "US 0").normalized


def test_known_mm_of_a_mm_size_is_read_from_the_notation() -> None:
    assert size(NeedleSystem.MM, "4 mm").known_mm == Decimal(4)


def test_known_mm_of_a_us_size_is_absent_without_input() -> None:
    assert size(NeedleSystem.US, "US 6").known_mm is None


def test_known_mm_of_a_us_size_is_the_input() -> None:
    assert size(NeedleSystem.US, "US 6", Decimal(4)).known_mm == Decimal(4)


def test_known_mm_of_a_jp_size_is_not_converted() -> None:
    assert size(NeedleSystem.JP, "6号").known_mm is None


def test_mm_input_accepts_a_decimal_and_none() -> None:
    assert size(NeedleSystem.US, "US 6", Decimal(4)).mm == Decimal(4)
    assert size(NeedleSystem.US, "US 6", None).mm is None


@pytest.mark.parametrize("mm", [4.0, 0, 100000])
def test_mm_input_refuses_a_float_zero_and_too_many_digits(mm: object) -> None:
    with pytest.raises(ValidationError):
        NeedleSize.model_validate({"system": "us", "original": "US 6", "mm": mm})


@pytest.mark.parametrize(
    ("system", "original"),
    [
        (NeedleSystem.US, "10.5"),
        (NeedleSystem.US, "10,5"),
        (NeedleSystem.US, "US 10 1/2"),
        (NeedleSystem.US, "10¾"),
        (NeedleSystem.US, "1\uff16"),
        (NeedleSystem.JP, "6.5"),
        (NeedleSystem.US, "UK 8"),
        (NeedleSystem.UK, "US 6"),
        (NeedleSystem.MM, "0 mm"),
        (NeedleSystem.MM, "123456 mm"),
        (NeedleSystem.MM, "abc"),
        (NeedleSystem.US, ""),
    ],
)
def test_a_badly_formed_size_is_refused(system: NeedleSystem, original: str) -> None:
    with pytest.raises(ValidationError):
        size(system, original)


def test_a_mm_size_contradicted_by_its_input_is_refused() -> None:
    with pytest.raises(ValidationError):
        size(NeedleSystem.MM, "4 mm", Decimal("3.75"))


def test_a_mm_size_confirmed_by_its_input_is_accepted() -> None:
    assert size(NeedleSystem.MM, "4 mm", Decimal("4.0")).known_mm == Decimal(4)


def test_needle_size_refuses_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        NeedleSize.model_validate({"system": "us", "original": "US 6", "extra": 1})
