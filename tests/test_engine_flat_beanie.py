"""Bonnet à plat : lisières et diminutions à l’endroit (CLA-68, ADR 0028)."""

import datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.construction import CrownRule
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.pattern import Pattern, Repeat, Round, Stitch, Work
from knitproof.domain.provenance import SourceKind
from knitproof.engine.cast_on import flat_cast_on
from knitproof.engine.crown import crown_plan, crown_review
from knitproof.engine.verification import simulate, verify

RULE = CrownRule.model_validate(
    {
        "id": "calotte",
        "source": {
            "kind": SourceKind.PERSON_DECISION,
            "reference": "Isabelle, ADR 0019",
            "read_on": datetime.date(2026, 11, 2),
        },
        "decreases_per_round": 8,
        "last_round_below": 24,
        "min_cast_on": 32,
        "every_round_last": 3,
    }
)
SWATCH = SwatchMeasurement(
    stitches=Decimal(20), width=Length(value=Decimal(10), unit=LengthUnit.CM)
)
RIBBING = StitchMultiple(repeat_multiple=4, repeat_offset=0)


def test_a_flat_cast_on_adds_two_selvedges_to_a_multiple_of_four() -> None:
    result = flat_cast_on(Length(value=Decimal(44), unit=LengthUnit.CM), SWATCH, RIBBING)

    assert (result.body.stitches, result.selvedges, result.total) == (88, 2, 90)


def test_the_finished_round_is_measured_on_the_88_stitches() -> None:
    result = flat_cast_on(Length(value=Decimal(44), unit=LengthUnit.CM), SWATCH, RIBBING)

    assert result.body.finished_cm == Decimal(44)


def test_a_flat_crown_of_88_has_2n_minus_1_rounds() -> None:
    crown = crown_plan(88, RULE, flat=True)

    assert (crown.decrease_rounds, crown.round_count, crown.remaining) == (10, 19, 8)
    assert crown.stitches == 88


def test_a_flat_crown_decreases_on_odd_rounds_only() -> None:
    crown = crown_plan(88, RULE, flat=True)

    for round_ in crown.rounds:
        assert (Stitch.K2TOG in _kinds(round_)) == (round_.start % 2 == 1)


def test_every_flat_round_starts_and_ends_with_a_selvedge_stitch() -> None:
    crown = crown_plan(88, RULE, flat=True)

    assert all(r.ops[0] == Work(work=1) and r.ops[-1] == Work(work=1) for r in crown.rounds)


def test_a_flat_crown_runs_from_90_stitches_to_the_closing_round() -> None:
    crown = crown_plan(88, RULE, flat=True)

    counts = simulate(Pattern(cast_on=90, rounds=crown.rounds)).counts

    assert counts[-1].stitches == crown.remaining + 2


def test_a_flat_crown_passes_verification() -> None:
    crown = crown_plan(88, RULE, flat=True)

    assert verify(Pattern(cast_on=90, rounds=crown.rounds)) == []


def test_a_flat_crown_review_has_no_notice_on_an_even_count() -> None:
    review = crown_review(88, RULE, flat=True)

    assert review.crown == crown_plan(88, RULE, flat=True)
    assert review.notices == ()


def _kinds(round_: Round) -> set[object]:
    kinds: set[object] = set()
    for op in round_.ops:
        if isinstance(op, Repeat):
            kinds.update(op.repeat.body)
        else:
            kinds.add(op)
    return kinds


@given(stitches=st.integers(min_value=32, max_value=400))
def test_a_flat_crown_is_verified_for_every_cast_on(stitches: int) -> None:
    crown = crown_plan(stitches, RULE, flat=True)

    assert crown.round_count == 2 * crown.decrease_rounds - 1
    assert verify(Pattern(cast_on=stitches + 2, rounds=crown.rounds)) == []
