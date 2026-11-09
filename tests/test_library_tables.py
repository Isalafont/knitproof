"""Les tables de `library/data/` rendent les valeurs sourcées de leurs ADR (CLA-67)."""

from decimal import Decimal

import pytest

from knitproof.domain.age import Age, AgeUnit
from knitproof.domain.ease import EaseSource, EdgeStitch, Fit
from knitproof.domain.head_size import Sex
from knitproof.domain.measure import LengthUnit
from knitproof.domain.provenance import SourceKind
from knitproof.domain.reference import ReferenceMeasurement
from knitproof.library.loader import Library, load_library
from knitproof.library.lookup import head_ranges_for, rows_for_age


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


def heights_of(library: Library, age: Age) -> list[tuple[str, Decimal]]:
    found = rows_for_age(library, age)
    assert all(item.value is not None and item.value.unit is LengthUnit.IN for item in found)
    return [(item.id, item.value.value) for item in found if item.value is not None]


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (
            months(6),
            [("baby-3-6-mois", Decimal(7)), ("baby-6-12-mois", Decimal("7.5"))],
        ),
        (
            months(12),
            [
                ("baby-6-12-mois", Decimal("7.5")),
                ("toddler-12-mois-3-ans", Decimal(8)),
            ],
        ),
        (
            years(3),
            [
                ("toddler-12-mois-3-ans", Decimal(8)),
                ("child-3-10-ans", Decimal("8.5")),
            ],
        ),
        (years(4), [("child-3-10-ans", Decimal("8.5"))]),
        (months(4), [("baby-3-6-mois", Decimal(7))]),
    ],
)
def test_ages_with_two_heights_give_both_rows_in_inches(
    library: Library, age: Age, expected: list[tuple[str, Decimal]]
) -> None:
    assert heights_of(library, age) == expected


def test_an_age_beyond_the_numbered_rows_gives_no_row(library: Library) -> None:
    assert rows_for_age(library, years(30)) == ()


def test_the_twelve_rows_are_in_inches_and_to_verify(library: Library) -> None:
    rows = [r for r in library.entries_of(ReferenceMeasurement) if r.quantity.value == "height"]

    assert [r.value.value for r in rows if r.value is not None] == [
        Decimal(x)
        for x in ("3.5", "4", "4.5", "5", "6", "7", "7.5", "8", "8.5", "10", "11", "11.5")
    ]
    assert all(r.source.to_verify and "Knit Picks" in r.source.reference for r in rows)
    assert all(r.source.read_on.isoformat() == "2026-11-02" for r in rows)
    assert [r.age is not None for r in rows].count(True) == 4


def ease_source(library: Library, source_id: str) -> EaseSource:
    [found] = [item for item in library.entries_of(EaseSource) if item.id == source_id]
    return found


def test_oslo_has_seven_sizes_with_head_range_and_cast_on(library: Library) -> None:
    oslo = ease_source(library, "oslo-ajuste-jersey")

    assert [size.cast_on for size in oslo.sizes] == [92, 96, 100, 104, 108, 112, 120]
    assert [(size.head.low, size.head.high) for size in oslo.sizes] == [
        (Decimal(low), Decimal(high))
        for low, high in [(47, 48), (49, 50), (51, 52), (53, 54), (55, 56), (57, 59), (60, 63)]
    ]
    assert all(size.head.unit is LengthUnit.CM for size in oslo.sizes)
    assert oslo.swatch is not None
    assert oslo.swatch.measurement.stitches_per_10_cm == Decimal(23)
    assert (oslo.fit, oslo.edge) == (Fit.FITTED, EdgeStitch.STOCKINETTE)
    assert oslo.source.to_verify is True
    assert oslo.source.read_on.isoformat() == "2026-11-05"
    assert "PetiteKnit" in oslo.source.reference


def test_rosebud_has_one_size_in_inches_with_the_published_brim(library: Library) -> None:
    rosebud = ease_source(library, "rosebud-ample-cotes-2-2")
    [size] = rosebud.sizes

    assert (size.head.low, size.head.high, size.head.unit) == (
        Decimal(20),
        Decimal("23.75"),
        LengthUnit.IN,
    )
    assert size.brim_circumference is not None
    assert (size.brim_circumference.value, size.brim_circumference.unit) == (
        Decimal(18),
        LengthUnit.IN,
    )
    assert rosebud.swatch is None
    assert (rosebud.fit, rosebud.edge) == (Fit.LOOSE, EdgeStitch.RIB_2X2)
    assert "Brooklyn Tweed" in rosebud.source.reference
