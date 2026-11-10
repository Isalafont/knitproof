"""Propriétés de la calotte en rond (CLA-68, ADR 0019)."""

import datetime

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.construction import CrownRule
from knitproof.domain.pattern import Pattern, Repeat, Round, Stitch, Work
from knitproof.domain.provenance import SourceKind
from knitproof.engine.crown import crown_plan
from knitproof.engine.verification import verify

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
STITCHES = st.integers(min_value=32, max_value=400)


@given(stitches=STITCHES)
def test_the_crown_has_twice_the_decrease_rounds_minus_three(stitches: int) -> None:
    crown = crown_plan(stitches, RULE)

    assert crown.round_count == 2 * crown.decrease_rounds - 3
    assert sum(1 for r in crown.rounds if Stitch.K2TOG in _kinds(r)) == crown.decrease_rounds


@given(stitches=STITCHES)
def test_the_last_round_leaves_8_to_12_stitches(stitches: int) -> None:
    assert 8 <= crown_plan(stitches, RULE).remaining <= 12


@given(stitches=STITCHES)
def test_the_remainder_is_spread_by_the_formula_of_rule_2(stitches: int) -> None:
    crown = crown_plan(stitches, RULE)
    count = stitches
    for round_ in crown.rounds[:-1]:
        if Stitch.K2TOG in _kinds(round_):
            expected = [
                count // 8 + (i + 1) * (count % 8) // 8 - i * (count % 8) // 8 for i in range(8)
            ]
            assert _sections(round_) == expected
            count -= 8


@given(stitches=STITCHES)
def test_the_crown_passes_verification(stitches: int) -> None:
    crown = crown_plan(stitches, RULE)

    assert verify(Pattern(cast_on=stitches, rounds=crown.rounds)) == []


def _kinds(round_: Round) -> set[object]:
    kinds: set[object] = set()
    for op in round_.ops:
        if isinstance(op, Repeat):
            kinds.update(op.repeat.body)
        else:
            kinds.add(op)
    return kinds


def _sections(round_: Round) -> list[int]:
    """Taille de chaque section : mailles tricotées avant le `k2tog`, plus ses deux."""
    flat: list[object] = []
    for op in round_.ops:
        if isinstance(op, Repeat):
            flat.extend(list(op.repeat.body) * op.repeat.times)
        else:
            flat.append(op)
    sizes: list[int] = []
    worked = 0
    for item in flat:
        if isinstance(item, Work):
            worked += item.work
        else:
            sizes.append(worked + 2)
            worked = 0
    return sizes
