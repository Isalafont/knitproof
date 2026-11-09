"""Les tables de `library/data/` rendent les valeurs sourcées de leurs ADR (CLA-67)."""

from decimal import Decimal

import pytest

from knitproof.domain.age import Age, AgeUnit
from knitproof.domain.head_size import Sex
from knitproof.domain.measure import LengthUnit
from knitproof.domain.provenance import SourceKind
from knitproof.domain.reference import ReferenceMeasurement
from knitproof.library.loader import Library, load_library
from knitproof.library.lookup import head_ranges_for


@pytest.fixture(scope="module")
def library() -> Library:
    return load_library()


def months(value: int) -> Age:
    return Age(value=value, unit=AgeUnit.MONTHS)


def years(value: int) -> Age:
    return Age(value=value, unit=AgeUnit.YEARS)


def bounds(measurement: ReferenceMeasurement) -> tuple[Decimal | None, Decimal]:
    assert measurement.span is not None
    assert measurement.span.unit is LengthUnit.CM
    return measurement.span.low, measurement.span.high


def head_of(library: Library, age: Age, sex: Sex | None = None) -> tuple[Decimal | None, Decimal]:
    [found] = head_ranges_for(library, age, sex)
    return bounds(found)


def test_three_years_gives_a_range_with_its_patterns_and_no_proposed_value(
    library: Library,
) -> None:
    [found] = head_ranges_for(library, years(3))

    assert bounds(found) == (Decimal(50), Decimal(52))
    assert found.source.kind is SourceKind.REFERENCE_MEASUREMENT
    assert found.source.to_verify is True
    assert "DROPS Children 49-25" in found.source.reference
    assert "37-16" in found.source.reference
    assert "proposed" not in "".join(ReferenceMeasurement.model_fields)


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (months(0), (None, Decimal(35))),
        (months(2), (None, Decimal(35))),
        (months(3), (Decimal(35), Decimal(40))),
        (months(5), (Decimal(35), Decimal(40))),
        (months(6), (Decimal(40), Decimal(45))),
        (months(11), (Decimal(40), Decimal(45))),
        (months(12), (Decimal(44), Decimal(46))),
        (months(18), (Decimal(44), Decimal(46))),
        (months(19), (Decimal(45), Decimal(48))),
        (months(23), (Decimal(45), Decimal(48))),
        (years(2), (Decimal(48), Decimal(50))),
        (years(3), (Decimal(50), Decimal(52))),
        (years(4), (Decimal(50), Decimal(52))),
        (years(5), (Decimal(52), Decimal(53))),
        (years(6), (Decimal(52), Decimal(53))),
        (years(7), (Decimal(53), Decimal(54))),
        (years(8), (Decimal(53), Decimal(54))),
        (years(9), (Decimal(54), Decimal(55))),
        (years(10), (Decimal(54), Decimal(55))),
        (years(11), (Decimal(55), Decimal(56))),
        (years(12), (Decimal(55), Decimal(56))),
        (years(13), (Decimal(56), Decimal(57))),
        (years(14), (Decimal(56), Decimal(57))),
    ],
)
def test_each_age_falls_in_exactly_one_slice(
    library: Library, age: Age, expected: tuple[Decimal | None, Decimal]
) -> None:
    assert head_of(library, age) == expected


def test_a_slice_boundary_goes_to_the_older_slice(library: Library) -> None:
    assert head_of(library, months(18)) == (Decimal(44), Decimal(46))
    assert head_of(library, months(19)) == (Decimal("45"), Decimal("48"))
    assert head_of(library, years(2)) == (Decimal(48), Decimal(50))
    assert head_of(library, years(3)) == (Decimal(50), Decimal(52))


def test_from_fifteen_years_the_range_follows_the_sex(library: Library) -> None:
    assert head_of(library, years(15), Sex.FEMALE) == (Decimal("53"), Decimal("58.5"))
    assert head_of(library, years(40), Sex.MALE) == (Decimal(56), Decimal(61))


def test_from_fifteen_years_without_sex_both_ranges_are_given(library: Library) -> None:
    found = head_ranges_for(library, years(30))

    assert sorted(bounds(item) for item in found) == [
        (Decimal(53), Decimal("58.5")),
        (Decimal(56), Decimal(61)),
    ]
    assert all("Craft Yarn Council" in item.source.reference for item in found)
    assert all(
        "craftyarncouncil.com/standards/head-circumference-chart" in item.source.reference
        for item in found
    )


def test_a_child_age_ignores_the_sex(library: Library) -> None:
    assert head_of(library, years(3), Sex.FEMALE) == head_of(library, years(3), Sex.MALE)


def test_every_head_slice_is_to_verify_with_a_pattern_or_the_council(library: Library) -> None:
    found = [
        item
        for item in library.entries_of(ReferenceMeasurement)
        if item.quantity.value == "head_circumference"
    ]

    assert len(found) == 14
    assert all(item.source.to_verify for item in found)
    assert all(
        any(name in item.source.reference for name in ("DROPS", "Julie Taylor", "Craft Yarn"))
        for item in found
    )
