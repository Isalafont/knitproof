"""Propriétés du calcul d’aisance de référence (CLA-67, ADR 0024)."""

import datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.ease import EaseSource, EdgeStitch, Fit
from knitproof.engine.ease import propose_ease, reference_ease

HEADS = st.integers(min_value=30, max_value=70)
SIZES = st.builds(
    lambda low, extra, cast_on: {
        "head": {"low": str(low), "high": str(low + extra), "unit": "cm"},
        "cast_on": cast_on,
    },
    HEADS,
    st.integers(min_value=0, max_value=5),
    st.integers(min_value=20, max_value=300),
)
SWATCHES = st.builds(
    lambda stitches, width: {
        "stitches": str(stitches),
        "width": {"value": str(width), "unit": "cm"},
        "stitch": "stockinette",
    },
    st.integers(min_value=10, max_value=40),
    st.integers(min_value=5, max_value=15),
)
SOURCES = st.builds(
    lambda sizes, swatch: EaseSource.model_validate(
        {
            "id": "t",
            "fit": "fitted",
            "edge": "stockinette",
            "swatch": swatch,
            "sizes": sizes,
            "source": {
                "kind": "reference_measurement",
                "reference": "x",
                "read_on": datetime.date(2026, 11, 9),
            },
        }
    ),
    st.lists(SIZES, min_size=1, max_size=8),
    SWATCHES,
)


@given(SOURCES)
def test_the_proposed_value_stays_within_the_range(source: EaseSource) -> None:
    proposal = reference_ease(source)

    assert proposal.low <= proposal.proposed <= proposal.high


@given(SOURCES)
def test_the_range_covers_every_size(source: EaseSource) -> None:
    proposal = reference_ease(source)

    assert len(proposal.by_size) == len(source.sizes)
    assert all(proposal.low <= value <= proposal.high for value in proposal.by_size)


@given(SOURCES)
def test_no_value_is_a_float(source: EaseSource) -> None:
    proposal = reference_ease(source)

    values = [proposal.proposed, proposal.low, proposal.high, *proposal.by_size]
    assert all(type(value) is Decimal for value in values)


@given(SOURCES)
def test_the_same_source_gives_the_same_proposal(source: EaseSource) -> None:
    assert reference_ease(source) == reference_ease(source)


@given(st.lists(SOURCES, min_size=1, max_size=5))
def test_the_proposed_value_lies_in_its_range_and_ignores_the_order(
    sources: list[EaseSource],
) -> None:
    outcome = propose_ease(
        sources, (), (), Fit.FITTED, EdgeStitch.STOCKINETTE, EdgeStitch.STOCKINETTE, None
    )
    reversed_outcome = propose_ease(
        sources[::-1], (), (), Fit.FITTED, EdgeStitch.STOCKINETTE, EdgeStitch.STOCKINETTE, None
    )

    assert outcome.value is not None
    assert outcome.low is not None
    assert outcome.high is not None
    assert outcome.low <= outcome.value <= outcome.high
    assert outcome.value == reversed_outcome.value
    assert (outcome.low, outcome.high) == (reversed_outcome.low, reversed_outcome.high)
