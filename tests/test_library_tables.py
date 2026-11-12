"""Les tables de `library/data/` rendent les valeurs sourcées de leurs ADR (CLA-67)."""

import unicodedata
from decimal import Decimal
from pathlib import Path

import pytest

from knitproof.domain.age import Age, AgeUnit
from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.ease import EaseSource, EdgeStitch, Fit
from knitproof.domain.fiber import Fiber, name_key
from knitproof.domain.head_size import Sex
from knitproof.domain.measure import LengthUnit
from knitproof.domain.needle import NeedleSize, NeedleSystem, NeedleTableRow
from knitproof.domain.provenance import SourceKind
from knitproof.domain.reference import ReferenceMeasurement
from knitproof.domain.yarn import Yarn
from knitproof.library.loader import Library, load_library
from knitproof.library.lookup import fiber_named, head_ranges_for, needle_rows, rows_for_age


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


def needle(system: NeedleSystem, original: str) -> NeedleSize:
    return NeedleSize(system=system, original=original)


def test_us_6_gives_4_and_4_25_mm_from_the_craft_yarn_council(library: Library) -> None:
    [row] = needle_rows(library, needle(NeedleSystem.US, "6"))

    assert row.mm == (Decimal(4), Decimal("4.25"))
    assert "Craft Yarn Council" in row.source.reference
    assert row.source.to_verify is True


def test_uk_00_gives_9_mm_to_verify(library: Library) -> None:
    [row] = needle_rows(library, needle(NeedleSystem.UK, "00"))

    assert row.mm == (Decimal(9),)
    assert row.source.to_verify is True
    assert "Sheep and Stitch" in row.source.reference


def test_jp_15_gives_6_6_mm_from_clover(library: Library) -> None:
    [row] = needle_rows(library, needle(NeedleSystem.JP, "15"))

    assert row.mm == (Decimal("6.6"),)
    assert "Clover" in row.source.reference


def test_a_size_missing_from_the_table_gives_no_row(library: Library) -> None:
    assert needle_rows(library, needle(NeedleSystem.US, "37")) == ()
    assert needle_rows(library, needle(NeedleSystem.MM, "3.6")) == ()


def test_the_whole_jp_table_is_to_verify(library: Library) -> None:
    jp = [row for row in library.entries_of(NeedleTableRow) if row.system is NeedleSystem.JP]

    assert len(jp) == 16
    assert all(row.source.to_verify for row in jp)


def test_the_tables_have_the_rows_of_adr_0021(library: Library) -> None:
    rows = library.entries_of(NeedleTableRow)
    counts = {system: sum(row.system is system for row in rows) for system in NeedleSystem}

    assert counts == {
        NeedleSystem.US: 22,
        NeedleSystem.UK: 17,
        NeedleSystem.JP: 16,
        NeedleSystem.MM: 0,
    }


def test_the_crown_values_are_loaded_as_a_person_decision_of_adr_0019(library: Library) -> None:
    [crown] = library.entries_of(CrownRule)

    assert (
        crown.decreases_per_round,
        crown.last_round_below,
        crown.min_cast_on,
        crown.every_round_last,
    ) == (8, 24, 32, 3)
    assert crown.source.kind is SourceKind.PERSON_DECISION
    assert "ADR 0019" in crown.source.reference
    assert crown.source.read_on.isoformat() == "2026-11-02"


def test_the_magic_loop_cable_is_an_advice_with_its_two_sources(library: Library) -> None:
    [advice] = library.entries_of(MagicLoopAdvice)

    assert advice.magic_loop_cable.value == Decimal(80)
    assert advice.magic_loop_cable.unit is LengthUnit.CM
    assert advice.role == "advice"
    assert "KnitPro" in advice.source.reference
    assert "Knit Picks" in advice.source.reference


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("alpaga", "alpaca"),
        ("Alpaca", "alpaca"),
        ("MERINOULL", "merino"),
        ("merinould", "merino"),
        ("nylon", "nylon"),
        ("Polyamide", "polyamide"),
        ("Soie", "silk"),
    ],
)
def test_a_fiber_is_found_by_any_of_its_names(library: Library, name: str, expected: str) -> None:
    found = fiber_named(library, name)

    assert found is not None
    assert found.id == expected


def test_an_unknown_fiber_name_gives_none(library: Library) -> None:
    assert fiber_named(library, "angora") is None


def test_the_accent_is_kept_and_the_unicode_form_ignored_in_a_lookup(tmp_path: Path) -> None:
    (tmp_path / "0030-fibres.yaml").write_text(
        "schema_version: 1\n"
        "decided_in: docs/adr/0030-laines-de-reference.md\n"
        "entries:\n"
        "  - id: merino\n"
        "    names: [mérinos]\n"
        "    source: {kind: person_decision, reference: test, read_on: 2026-11-12}\n",
        encoding="utf-8",
    )
    loaded = load_library(tmp_path, registry={"0030-fibres.yaml": Fiber})

    assert fiber_named(loaded, unicodedata.normalize("NFD", "mérinos")) is not None
    assert fiber_named(loaded, "merinos") is None


def test_the_fibers_are_a_person_decision_of_adr_0030(library: Library) -> None:
    fibers = library.entries_of(Fiber)

    assert fibers
    assert all(fiber.source.kind is SourceKind.PERSON_DECISION for fiber in fibers)
    assert all("12/11/2026" in fiber.source.reference for fiber in fibers)


def test_a_fiber_added_to_a_directory_loads_without_code_change(tmp_path: Path) -> None:
    (tmp_path / "0030-fibres.yaml").write_text(
        "schema_version: 1\n"
        "decided_in: docs/adr/0030-laines-de-reference.md\n"
        "entries:\n"
        "  - id: angora\n"
        "    names: [angora]\n"
        "    source:\n"
        "      kind: person_decision\n"
        "      reference: test\n"
        "      read_on: 2026-11-12\n",
        encoding="utf-8",
    )

    added = load_library(tmp_path, registry={"0030-fibres.yaml": Fiber})

    assert fiber_named(added, "Angora") is not None


# Les laines citées par les patrons (ADR 0030) : dans le YAML, ou nommées ici avec leur raison.
# La liste vit dans ce test, indépendante du YAML.
EXPECTED_YARNS = frozenset(
    {
        "drops-merino-extra-fine",
        "drops-baby-merino",
        "drops-air",
        "drops-lima",
        "drops-kid-silk",
        "drops-fiesta",
        "madelinetosh-tosh-vintage",
        "brooklyn-tweed-shelter",
        "brooklyn-tweed-arbor",
        "de-rerum-natura-gilliatt",
        "rainbow-heirloom-sweater",
        "the-uncommon-thread-uncommon-everyday",
        "the-uncommon-thread-bfl-fingering",
        "purl-soho-daily-wool-worsted",
        "purl-soho-worsted-twist",
        "blue-sky-fibers-organic-cotton-skinny",
        "sandnes-garn-sunday",
        "sandnes-garn-double-sunday",
        "sandnes-garn-tynn-silk-mohair",
        "filcolana-arwetta",
        "sweet-fiber-cashmerino-worsted",
        "la-bien-aimee-merino-aran",
        "isager-silk-mohair",
        "von-broich-brushed-lace",
    }
)
NOT_YET_READ = "non encore relue"
MISSING_YARNS: dict[str, str] = {
    yarn_id: NOT_YET_READ
    for yarn_id in (
        "madelinetosh-tosh-vintage",
        "brooklyn-tweed-shelter",
        "brooklyn-tweed-arbor",
        "de-rerum-natura-gilliatt",
        "rainbow-heirloom-sweater",
        "the-uncommon-thread-uncommon-everyday",
        "the-uncommon-thread-bfl-fingering",
        "purl-soho-daily-wool-worsted",
        "purl-soho-worsted-twist",
        "blue-sky-fibers-organic-cotton-skinny",
        "sweet-fiber-cashmerino-worsted",
        "la-bien-aimee-merino-aran",
        "isager-silk-mohair",
        "von-broich-brushed-lace",
    )
}


def yarn_of(library: Library, yarn_id: str) -> Yarn:
    [found] = [yarn for yarn in library.entries_of(Yarn) if yarn.id == yarn_id]
    return found


def test_every_expected_yarn_is_loaded_or_named_as_missing(library: Library) -> None:
    loaded = {yarn.id for yarn in library.entries_of(Yarn)}

    assert loaded | MISSING_YARNS.keys() >= EXPECTED_YARNS
    assert loaded <= EXPECTED_YARNS


def test_a_missing_yarn_is_not_loaded_and_has_a_reason(library: Library) -> None:
    loaded = {yarn.id for yarn in library.entries_of(Yarn)}

    assert not loaded & MISSING_YARNS.keys()
    assert all(MISSING_YARNS.values())


def test_kid_silk_is_75_mohair_25_silk(library: Library) -> None:
    parts = yarn_of(library, "drops-kid-silk").composition.parts

    assert [(part.fiber, part.percent) for part in parts] == [
        ("mohair", Decimal(75)),
        ("silk", Decimal(25)),
    ]


def test_arwetta_is_80_merino_20_nylon(library: Library) -> None:
    yarn = yarn_of(library, "filcolana-arwetta")

    assert [(p.fiber, p.percent, p.label_term) for p in yarn.composition.parts] == [
        ("merino", Decimal(80), "merinould"),
        ("nylon", Decimal(20), "nylon"),
    ]
    assert yarn.status is None
    assert yarn.superwash is True


def test_the_yarn_sources_are_the_manufacturer_page_read_on_12_november(library: Library) -> None:
    for yarn in library.entries_of(Yarn):
        assert yarn.source.kind is SourceKind.REFERENCE_MEASUREMENT
        assert yarn.source.reference.startswith("https://")
        assert yarn.source.read_on.isoformat() == "2026-11-12"
        assert yarn.swatches == ()


def test_a_value_the_page_does_not_give_stays_absent(library: Library) -> None:
    sandnes = ("sandnes-garn-sunday", "sandnes-garn-double-sunday", "sandnes-garn-tynn-silk-mohair")

    assert yarn_of(library, "sandnes-garn-tynn-silk-mohair").label.care is None
    assert yarn_of(library, "drops-kid-silk").superwash is None
    for yarn_id in sandnes:
        gauge = yarn_of(library, yarn_id).label.gauge
        assert gauge is not None
        assert gauge.rows is None
        assert gauge.height is None


def test_the_sandnes_gauges_come_from_the_ravelry_page_in_stitches_per_4_inches(
    library: Library,
) -> None:
    sunday = yarn_of(library, "sandnes-garn-sunday")

    assert sunday.label.gauge is not None
    assert sunday.label.gauge.stitches == Decimal(28)
    assert sunday.label.gauge.width.unit is LengthUnit.IN
    assert sunday.label.gauge.width.value == Decimal(4)
    assert sunday.label.care is not None
    assert sunday.label.care.startswith("Vasker du i maskin")
    assert sunday.source.reference == "https://www.sandnesgarn.no/sunday"
    assert "ravelry.com/yarns/library/sandnes-garn-sunday" in (sunday.source.location or "")
    assert "pas par l’API" in (sunday.source.location or "")


def test_a_yarn_added_to_a_directory_loads_without_code_change(tmp_path: Path) -> None:
    fibers = (
        "schema_version: 1\n"
        "decided_in: docs/adr/0030-laines-de-reference.md\n"
        "entries:\n"
        "  - id: wool\n"
        "    names: [Laine]\n"
        "    source: {kind: person_decision, reference: test, read_on: 2026-11-12}\n"
    )
    yarns = (
        "schema_version: 1\n"
        "decided_in: docs/adr/0030-laines-de-reference.md\n"
        "entries:\n"
        "  - id: new-yarn\n"
        "    brand: Marque\n"
        "    name: Nouvelle\n"
        "    composition: {parts: [{fiber: wool, label_term: Laine, percent: 100}]}\n"
        "    superwash: null\n"
        "    label: {}\n"
        "    source: {kind: reference_measurement, reference: test, read_on: 2026-11-12}\n"
    )
    (tmp_path / "0030-fibres.yaml").write_text(fibers, encoding="utf-8")
    (tmp_path / "0030-laines-de-reference.yaml").write_text(yarns, encoding="utf-8")

    added = load_library(
        tmp_path, registry={"0030-fibres.yaml": Fiber, "0030-laines-de-reference.yaml": Yarn}
    )

    assert [yarn.id for yarn in added.entries_of(Yarn)] == ["new-yarn"]


def test_the_drops_merino_yarns_are_merino_as_the_page_title_writes_it(library: Library) -> None:
    for yarn_id in ("drops-merino-extra-fine", "drops-baby-merino"):
        yarn = yarn_of(library, yarn_id)

        assert [(p.fiber, p.label_term, p.percent) for p in yarn.composition.parts] == [
            ("merino", "laine mérinos", Decimal(100))
        ]
        assert yarn.status is None
        assert yarn.superwash is True
    air = yarn_of(library, "drops-air")
    assert [(p.fiber, p.label_term) for p in air.composition.parts] == [
        ("alpaca", "Alpaga"),
        ("polyamide", "Polyamide"),
        ("merino", "laine mérinos"),
    ]
    assert air.status is None


def test_every_fiber_name_is_a_label_term_of_a_loaded_yarn(library: Library) -> None:
    terms = {
        (part.fiber, name_key(part.label_term))
        for yarn in library.entries_of(Yarn)
        for part in yarn.composition.parts
    }
    for fiber in library.entries_of(Fiber):
        for name in fiber.names:
            if (fiber.id, name_key(name)) not in terms:
                assert (fiber.id, name) == ("alpaca", "alpaca"), f"{fiber.id} : {name}"


def test_every_label_term_is_a_name_of_its_fiber(library: Library) -> None:
    names = {
        fiber.id: {name_key(name) for name in fiber.names} for fiber in library.entries_of(Fiber)
    }
    for yarn in library.entries_of(Yarn):
        for part in yarn.composition.parts:
            assert name_key(part.label_term) in names[part.fiber], f"{yarn.id} : {part.label_term}"


def test_the_yarn_weight_is_kept_as_written_by_the_maker_or_ravelry(library: Library) -> None:
    assert (
        yarn_of(library, "drops-kid-silk").label.yarn_weight == "A (23 - 26 mailles) / 2 ply / lace"
    )
    assert yarn_of(library, "drops-air").label.yarn_weight == (
        "C (16 - 19 mailles) / 10 ply / aran / worsted"
    )
    assert yarn_of(library, "filcolana-arwetta").label.yarn_weight == "Light Fingering"
    assert yarn_of(library, "sandnes-garn-sunday").label.yarn_weight == "Fingering (14 wpi)"
    assert yarn_of(library, "sandnes-garn-double-sunday").label.yarn_weight == "DK (11 wpi)"
    assert yarn_of(library, "sandnes-garn-tynn-silk-mohair").label.yarn_weight == "Lace"


def test_the_ten_yarns_have_a_yarn_weight(library: Library) -> None:
    assert all(yarn.label.yarn_weight for yarn in library.entries_of(Yarn))


def test_nylon_and_polyamide_are_two_different_fibers(library: Library) -> None:
    nylon = fiber_named(library, "nylon")
    polyamide = fiber_named(library, "Polyamide")

    assert nylon is not None
    assert polyamide is not None
    assert nylon.id != polyamide.id
