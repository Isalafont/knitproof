"""L’aisance de référence se calcule des données brutes de la source (CLA-67, ADR 0024 §7)."""

import datetime
from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_EVEN, Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.ease import (
    BaseEase,
    EaseOrigin,
    EaseOutcome,
    EaseProposal,
    EaseSource,
    EdgeStitch,
    Fit,
)
from knitproof.domain.yarn import Yarn
from knitproof.engine.ease import propose_ease, reference_ease
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
        {"stitches": "23", "width": {"value": "10", "unit": "cm"}, "stitch": "stockinette"},
    )

    assert reference_ease(found).proposed == Decimal(0)


def test_an_even_number_of_sizes_proposes_the_mean_of_the_two_in_the_middle() -> None:
    swatch = {
        "stitches": "20",
        "width": {"value": "10", "unit": "cm"},
        "stitch": "stockinette",
    }
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
    swatch = {"stitches": "10", "width": {"value": "5", "unit": "cm"}, "stitch": "stockinette"}
    size = {"head": {"low": "30", "high": "30", "unit": "cm"}, "cast_on": 20}

    proposal = reference_ease(build([size, size], swatch))

    assert proposal.low <= proposal.proposed <= proposal.high


# --- propose_ease : plusieurs patrons, point de l’échantillon, laine (CLA-116, ADR 0031) ---

HEAD_40 = {"low": "40", "high": "40", "unit": "cm"}


def pattern(
    source_id: str,
    cast_ons: Sequence[int],
    *,
    fit: str = "fitted",
    edge: str = "rib_2x2",
    swatch_stitch: str | None = "stockinette",
    yarns: Sequence[str] = (),
    role: str = "proposal",
) -> EaseSource:
    """Tête de 40 cm, 20 m = 10 cm : un montage de 76 m donne -5 %, 80 m donne 0 %."""
    swatch = (
        None
        if swatch_stitch is None
        else {"stitches": "20", "width": {"value": "10", "unit": "cm"}, "stitch": swatch_stitch}
    )
    return EaseSource.model_validate(
        {
            "id": source_id,
            "fit": fit,
            "edge": edge,
            "swatch": swatch,
            "yarns": list(yarns),
            "role": role,
            "role_reason": "repère" if role == "landmark" else None,
            "sizes": [{"head": HEAD_40, "cast_on": cast_on} for cast_on in cast_ons],
            "source": {"kind": "reference_measurement", "reference": "x", "read_on": READ_ON},
        }
    )


def yarn(yarn_id: str, fiber: str, *, superwash: bool | None) -> Yarn:
    return Yarn.model_validate(
        {
            "id": yarn_id,
            "brand": "b",
            "name": "n",
            "composition": {"parts": [{"fiber": fiber, "label_term": fiber, "percent": 100}]},
            "superwash": superwash,
            "label": {},
            "source": {"kind": "reference_measurement", "reference": "x", "read_on": READ_ON},
        }
    )


MERINO_SW = yarn("merino-sw", "merino", superwash=True)
MERINO_SW_BIS = yarn("merino-sw-bis", "merino", superwash=True)
ALPACA = yarn("alpaca", "alpaca", superwash=False)
YARNS = (MERINO_SW, MERINO_SW_BIS, ALPACA)
BASE = BaseEase.model_validate(
    {
        "id": "base",
        "fit": "fitted",
        "edges": ["rib_1x1", "rib_2x2"],
        "swatch_stitch": "stockinette",
        "value": "-5",
        "source": {"kind": "person_decision", "reference": "x", "read_on": READ_ON},
    }
)


def propose(
    sources: Sequence[EaseSource],
    *,
    yarn_id: str | None = "merino-sw",
    fit: Fit = Fit.FITTED,
    edge: EdgeStitch = EdgeStitch.RIB_2X2,
    swatch_stitch: EdgeStitch = EdgeStitch.STOCKINETTE,
) -> EaseOutcome:
    return propose_ease(sources, YARNS, (BASE,), fit, edge, swatch_stitch, yarn_id)


def test_matching_patterns_give_the_median_of_their_medians() -> None:
    sources = [
        pattern("a", [72, 76, 80], yarns=["merino-sw"]),  # médiane des tailles : -5
        pattern("b", [70], yarns=["merino-sw-bis"]),  # -12,5
        pattern("c", [78], yarns=["merino-sw"]),  # -2,5
    ]

    outcome = propose(sources)

    assert outcome.origin is EaseOrigin.SOURCES
    assert outcome.value == Decimal(-5)
    assert (outcome.low, outcome.high) == (Decimal("-12.5"), Decimal("-2.5"))
    assert (outcome.size_low, outcome.size_high) == (Decimal("-12.5"), Decimal(0))
    assert [item.source_id for item in outcome.sources] == ["a", "b", "c"]
    assert outcome.to_verify is True
    assert outcome.base is None


def test_an_even_number_of_patterns_takes_the_mean_of_the_two_in_the_middle() -> None:
    sources = [pattern("a", [72], yarns=["alpaca"]), pattern("b", [76], yarns=["alpaca"])]

    outcome = propose(sources, yarn_id="alpaca")

    assert outcome.value == Decimal("-7.5")


def test_a_single_matching_pattern_keeps_its_own_range() -> None:
    outcome = propose([pattern("a", [72, 76, 80])])

    assert outcome.value == Decimal(-5)
    assert (outcome.low, outcome.high) == (Decimal(-10), Decimal(0))


def test_a_pattern_of_another_yarn_family_does_not_count() -> None:
    sources = [pattern("a", [72], yarns=["alpaca"]), pattern("b", [76], yarns=["merino-sw"])]

    outcome = propose(sources)

    assert outcome.value == Decimal(-5)
    assert [item.source_id for item in outcome.sources] == ["b"]
    assert [item.source_id for item in outcome.landmarks] == ["a"]


def test_a_pattern_without_yarn_counts_for_any_yarn() -> None:
    outcome = propose([pattern("a", [72])], yarn_id="alpaca")

    assert outcome.value == Decimal(-10)


def test_a_pattern_without_swatch_counts_for_any_swatch_stitch() -> None:
    outcome = propose([rosebud_like()], swatch_stitch=EdgeStitch.RIB_2X2)

    assert outcome.origin is EaseOrigin.SOURCES
    assert outcome.value == Decimal(-5)


def rosebud_like() -> EaseSource:
    return EaseSource.model_validate(
        {
            "id": "r",
            "fit": "fitted",
            "edge": "rib_2x2",
            "sizes": [{"head": HEAD_40, "brim_circumference": {"value": "38", "unit": "cm"}}],
            "source": {"kind": "reference_measurement", "reference": "x", "read_on": READ_ON},
        }
    )


def test_a_landmark_never_enters_the_value() -> None:
    sources = [pattern("a", [76]), pattern("l", [60], role="landmark")]

    outcome = propose(sources)

    assert outcome.value == Decimal(-5)
    assert [item.source_id for item in outcome.landmarks] == ["l"]


def test_without_a_matching_pattern_the_base_applies_to_a_fitted_hat_in_ribs() -> None:
    outcome = propose([pattern("a", [72], yarns=["alpaca"])])

    assert outcome.origin is EaseOrigin.BASE
    assert outcome.value == Decimal(-5)
    assert outcome.base == BASE
    assert outcome.to_verify is True
    assert [item.source_id for item in outcome.landmarks] == ["a"]


def test_a_swatch_in_ribs_without_a_pattern_at_that_point_gives_no_value() -> None:
    sources = [pattern("a", [72]), pattern("l", [60], role="landmark")]

    outcome = propose(sources, swatch_stitch=EdgeStitch.RIB_2X2)

    assert outcome.origin is EaseOrigin.NONE
    assert outcome.value is None
    assert outcome.base is None
    assert outcome.to_verify is False
    assert {item.source_id for item in outcome.landmarks} == {"a", "l"}


def test_a_loose_hat_gets_no_base() -> None:
    outcome = propose([], fit=Fit.LOOSE)

    assert outcome.origin is EaseOrigin.NONE


def test_a_stockinette_edge_gets_no_base() -> None:
    outcome = propose([], edge=EdgeStitch.STOCKINETTE)

    assert outcome.origin is EaseOrigin.NONE


def test_no_yarn_cannot_match_a_pattern_that_names_yarns() -> None:
    outcome = propose([pattern("a", [72], yarns=["merino-sw"])], yarn_id=None)

    assert outcome.origin is EaseOrigin.BASE


def test_the_same_majority_fiber_with_another_superwash_does_not_match() -> None:
    untreated = yarn("merino-plain", "merino", superwash=False)
    sources = [pattern("a", [72], yarns=["merino-sw-bis"])]

    outcome = propose_ease(
        sources,
        (*YARNS, untreated),
        (BASE,),
        Fit.FITTED,
        EdgeStitch.RIB_2X2,
        EdgeStitch.STOCKINETTE,
        "merino-plain",
    )

    assert outcome.origin is EaseOrigin.BASE
    assert [item.source_id for item in outcome.landmarks] == ["a"]


def test_a_value_without_an_origin_is_refused() -> None:
    with pytest.raises(ValidationError, match="origine"):
        EaseOutcome(origin=EaseOrigin.NONE, value=Decimal(-5))
    with pytest.raises(ValidationError, match="origine"):
        EaseOutcome(origin=EaseOrigin.SOURCES)


def test_a_base_without_the_base_origin_is_refused() -> None:
    with pytest.raises(ValidationError, match="base"):
        EaseOutcome(origin=EaseOrigin.SOURCES, value=Decimal(-5), base=BASE)
    with pytest.raises(ValidationError, match="base"):
        EaseOutcome(origin=EaseOrigin.BASE, value=Decimal(-5))
