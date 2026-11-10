"""Aiguilles dans leur système d’origine, sans table de correspondance (CLA-104)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.measure import Length, LengthUnit
from knitproof.domain.needle import (
    KnittingMethod,
    Needle,
    NeedleCheck,
    NeedleKind,
    NeedleMaterial,
    NeedleSize,
    NeedleSystem,
)


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
        # ADR 0021, décision 8 : ½ se normalise en .5 en US.
        (NeedleSystem.US, "US 10½", "10.5"),
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
        # ADR 0021, décision 7 : virgule refusée en US et UK.
        (NeedleSystem.US, "10,5"),
        (NeedleSystem.UK, "10,5"),
        # ADR 0021, décision 7 : seules les fractions ½ et ¾ s’écrivent, pas « 1/2 ».
        (NeedleSystem.US, "US 10 1/2"),
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


@pytest.mark.parametrize(
    ("system", "original"),
    [
        (NeedleSystem.US, "10.5"),
        (NeedleSystem.US, "10¾"),
        (NeedleSystem.US, "2.5"),
        (NeedleSystem.US, "2½"),
        (NeedleSystem.US, "10.75"),
        (NeedleSystem.US, "000"),
        (NeedleSystem.UK, "10.5"),
        (NeedleSystem.UK, "2½"),
    ],
)
def test_decimals_and_halves_and_three_quarters_are_accepted(
    system: NeedleSystem, original: str
) -> None:
    # ADR 0021, décision 7 : décimales à point et fractions ½ et ¾.
    assert size(system, original).original == original


@pytest.mark.parametrize("a", ["2.5", "2½", "2.50", "US 2½"])
def test_us_decimal_and_half_normalize_alike(a: str) -> None:
    # ADR 0021, décision 8 : « 2.5 » et « 2½ » sont égaux en US.
    assert size(NeedleSystem.US, a).normalized == "2.5"


def test_us_three_quarters_normalizes_to_a_decimal() -> None:
    # ADR 0021, décision 8, ¾ : 10¾ vaut 10.75 (KnitPro).
    assert size(NeedleSystem.US, "10¾").normalized == size(NeedleSystem.US, "10.75").normalized


def test_us_integers_keep_their_trailing_zeros() -> None:
    assert size(NeedleSystem.US, "10").normalized == "10"


def test_the_original_notation_is_kept() -> None:
    assert size(NeedleSystem.US, "2½").original == "2½"


def test_uk_compares_by_notation() -> None:
    # ADR 0021, décision 8 : l’égalité 2.5 = 2½ est limitée au système US.
    assert size(NeedleSystem.UK, "2.5").normalized != size(NeedleSystem.UK, "2½").normalized


@pytest.mark.parametrize("other", ["00", "000"])
def test_us_zero_stays_distinct_from_double_and_triple_zero(other: str) -> None:
    # ADR 0021, décision 8 : « 00 » et « 000 » restent distincts de « 0 ».
    assert size(NeedleSystem.US, "0").normalized != size(NeedleSystem.US, other).normalized


def test_a_mm_size_contradicted_by_its_input_is_refused() -> None:
    with pytest.raises(ValidationError):
        size(NeedleSystem.MM, "4 mm", Decimal("3.75"))


def test_a_mm_size_confirmed_by_its_input_is_accepted() -> None:
    assert size(NeedleSystem.MM, "4 mm", Decimal("4.0")).known_mm == Decimal(4)


def test_needle_size_refuses_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        NeedleSize.model_validate({"system": "us", "original": "US 6", "extra": 1})


def cable() -> Length:
    return Length(value=Decimal(80), unit=LengthUnit.CM)


def needle(kind: NeedleKind, cable_length: Length | None = None) -> Needle:
    return Needle(size=size(NeedleSystem.MM, "4 mm"), kind=kind, cable_length=cable_length)


@pytest.mark.parametrize("length", [None, cable()])
def test_a_circular_needle_has_an_optional_cable(length: Length | None) -> None:
    assert needle(NeedleKind.CIRCULAR, length).cable_length == length


@pytest.mark.parametrize("kind", [NeedleKind.STRAIGHT, NeedleKind.DOUBLE_POINTED])
def test_a_non_circular_needle_refuses_a_cable(kind: NeedleKind) -> None:
    assert needle(kind).cable_length is None
    with pytest.raises(ValidationError):
        needle(kind, cable())


def test_needle_refuses_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Needle.model_validate(
            {"size": size(NeedleSystem.MM, "4 mm"), "kind": "straight", "extra": 1}
        )


def test_material_is_optional_and_closed() -> None:
    assert needle(NeedleKind.STRAIGHT).material is None
    assert {m.value for m in NeedleMaterial} == {
        "metal",
        "wood",
        "bamboo",
        "plastic",
        "carbon",
        "other",
    }
    with pytest.raises(ValidationError):
        Needle.model_validate(
            {"size": size(NeedleSystem.MM, "4 mm"), "kind": "straight", "material": "aluminium"}
        )


def test_knitting_method_has_exactly_two_values() -> None:
    assert {m.value for m in KnittingMethod} == {"flat", "round"}


def test_needle_check_refuses_an_unknown_field() -> None:
    a = needle(NeedleKind.STRAIGHT)
    with pytest.raises(ValidationError):
        NeedleCheck.model_validate({"swatch": a, "project": a, "reasons": (), "extra": 1})
