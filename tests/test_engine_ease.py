"""L’aisance de référence se calcule des données brutes de la source (CLA-67, ADR 0024 §7)."""

import datetime
from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_EVEN, Decimal

import pytest

from knitproof.domain.ease import EaseProposal, EaseSource, EdgeStitch, Fit
from knitproof.engine.ease import reference_ease
from knitproof.library.loader import load_library

TENTH = Decimal("0.1")
READ_ON = datetime.date(2026, 11, 9)


def reading(value: Decimal) -> Decimal:
    return value.quantize(TENTH, rounding=ROUND_HALF_EVEN)


def real(source_id: str) -> EaseSource:
    [found] = [item for item in load_library().entries_of(EaseSource) if item.id == source_id]
    return found


def build(sizes: Sequence[Mapping[str, object]], swatch: Mapping[str, object] | None) -> EaseSource:
    return EaseSource.model_validate(
        {
            "id": "t",
            "fit": "fitted",
            "edge": "stockinette",
            "swatch": swatch,
            "sizes": sizes,
            "source": {"kind": "reference_measurement", "reference": "x", "read_on": READ_ON},
        }
    )


def test_oslo_gives_the_seven_ease_values_of_the_adr() -> None:
    proposal = reference_ease(real("oslo-ajuste-jersey"))

    assert [reading(value) for value in proposal.by_size] == [
        Decimal(x) for x in ("-15.8", "-15.7", "-15.6", "-15.5", "-15.4", "-16.0", "-15.2")
    ]


def test_oslo_proposes_the_median_over_the_range_of_the_sizes() -> None:
    proposal = reference_ease(real("oslo-ajuste-jersey"))

    assert reading(proposal.proposed) == Decimal("-15.6")
    assert (reading(proposal.low), reading(proposal.high)) == (Decimal("-16.0"), Decimal("-15.2"))
    assert proposal.fit is Fit.FITTED
    assert proposal.edge is EdgeStitch.STOCKINETTE


def test_rosebud_takes_its_range_from_the_two_ends_of_the_head() -> None:
    proposal = reference_ease(real("rosebud-ample-cotes-2-2"))

    assert reading(proposal.proposed) == Decimal("-17.7")
    assert (reading(proposal.low), reading(proposal.high)) == (Decimal("-24.2"), Decimal("-10.0"))
    assert proposal.fit is Fit.LOOSE
    assert proposal.edge is EdgeStitch.RIB_2X2


def test_a_proposal_carries_its_source_and_stays_to_verify() -> None:
    proposal = reference_ease(real("oslo-ajuste-jersey"))

    assert proposal.source_id == "oslo-ajuste-jersey"
    assert proposal.provenance.to_verify is True
    assert "Oslo" in proposal.provenance.reference


def test_the_published_circumference_is_compared_in_the_same_unit_as_the_head() -> None:
    in_inches = build(
        [
            {
                "head": {"low": "20", "high": "20", "unit": "in"},
                "brim_circumference": {"value": "18", "unit": "in"},
            }
        ],
        None,
    )
    in_cm = build(
        [
            {
                "head": {"low": "50.8", "high": "50.8", "unit": "cm"},
                "brim_circumference": {"value": "45.72", "unit": "cm"},
            }
        ],
        None,
    )

    assert reference_ease(in_inches).proposed == reference_ease(in_cm).proposed == Decimal(-10)


def test_the_cast_on_gives_the_circumference_by_the_swatch() -> None:
    found = build(
        [{"head": {"low": "40", "high": "40", "unit": "cm"}, "cast_on": 92}],
        {"stitches": "23", "width": {"value": "10", "unit": "cm"}},
    )

    assert reference_ease(found).proposed == Decimal(0)


def test_an_even_number_of_sizes_proposes_the_mean_of_the_two_in_the_middle() -> None:
    swatch = {"stitches": "20", "width": {"value": "10", "unit": "cm"}}
    sizes = [
        {"head": {"low": "40", "high": "40", "unit": "cm"}, "cast_on": cast_on}
        for cast_on in (60, 70, 80, 100)
    ]

    proposal = reference_ease(build(sizes, swatch))

    assert proposal.by_size == (Decimal(-25), Decimal("-12.5"), Decimal(0), Decimal(25))
    assert proposal.proposed == Decimal("-6.25")


def test_no_value_is_a_float() -> None:
    proposal: EaseProposal = reference_ease(real("oslo-ajuste-jersey"))

    values = [proposal.proposed, proposal.low, proposal.high, *proposal.by_size]
    assert all(type(value) is Decimal for value in values)


@pytest.mark.parametrize("source_id", ["oslo-ajuste-jersey", "rosebud-ample-cotes-2-2"])
def test_the_proposal_lies_within_its_range(source_id: str) -> None:
    proposal = reference_ease(real(source_id))

    assert proposal.low <= proposal.proposed <= proposal.high


def test_two_equal_sizes_keep_the_proposal_inside_the_range() -> None:
    swatch = {"stitches": "10", "width": {"value": "5", "unit": "cm"}}
    size = {"head": {"low": "30", "high": "30", "unit": "cm"}, "cast_on": 20}

    proposal = reference_ease(build([size, size], swatch))

    assert proposal.low <= proposal.proposed <= proposal.high
