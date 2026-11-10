"""Calotte en rond, selon l’ADR 0019 (CLA-68)."""

import datetime

import pytest

from knitproof.domain.construction import CrownRule
from knitproof.domain.pattern import Op, Pattern, Round, Stitch, Work
from knitproof.domain.provenance import SourceKind
from knitproof.engine.crown import crown_plan
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


def _ops(*raw: object) -> tuple[Op, ...]:
    return Round.model_validate({"start": 1, "ops": raw}).ops


@pytest.mark.parametrize(
    ("stitches", "decreases", "rounds", "remaining"),
    [(88, 10, 17, 8), (92, 10, 17, 10), (91, 10, 17, 10)],
)
def test_the_crown_table_of_adr_0019(
    stitches: int, decreases: int, rounds: int, remaining: int
) -> None:
    crown = crown_plan(stitches, RULE)

    assert (crown.decrease_rounds, crown.round_count, crown.remaining) == (
        decreases,
        rounds,
        remaining,
    )
    assert simulate(Pattern(cast_on=stitches, rounds=crown.rounds)).counts[-1].stitches == remaining


def test_the_first_round_of_88_stitches_decreases_in_8_sections_of_11() -> None:
    crown = crown_plan(88, RULE)

    assert crown.rounds[0].ops == _ops({"repeat": {"body": ({"work": 9}, "k2tog"), "times": 8}})
    assert crown.rounds[0].stated_count == 80


def test_a_round_between_decreases_is_worked_even() -> None:
    crown = crown_plan(88, RULE)

    assert crown.rounds[1].ops == (Work(work=80),)
    assert crown.rounds[1].stated_count is None


def test_the_last_round_of_88_stitches_is_k2tog_everywhere() -> None:
    crown = crown_plan(88, RULE)

    assert crown.rounds[-1].ops == _ops({"repeat": {"body": ("k2tog",), "times": 8}})
    assert crown.rounds[-1].stated_count == 8


def test_an_odd_last_round_works_the_lone_stitch_plainly() -> None:
    crown = crown_plan(91, RULE)

    assert crown.rounds[-1].ops == _ops({"repeat": {"body": ("k2tog",), "times": 9}}, {"work": 1})
    assert crown.rounds[-1].stated_count == 10


def test_the_last_three_rounds_all_decrease() -> None:
    crown = crown_plan(88, RULE)

    assert all(Stitch.K2TOG in _flat(r) for r in crown.rounds[-3:])


def test_the_remainder_is_spread_between_the_sections() -> None:
    # 91 = 8 x 11 + 3 : sections de 11 ou 12 mailles, 3 de 12.
    first = crown_plan(91, RULE).rounds[0]

    assert sum(_flat_work(first)) + 2 * 8 == 91


def test_a_crown_below_the_minimum_is_refused() -> None:
    with pytest.raises(ValueError, match="32"):
        crown_plan(31, RULE)


def test_the_crown_passes_verification() -> None:
    crown = crown_plan(88, RULE)

    assert verify(Pattern(cast_on=88, rounds=crown.rounds)) == []


def _flat(round_: Round) -> list[object]:
    flat: list[object] = []
    for op in round_.ops:
        if hasattr(op, "repeat"):
            flat.extend(list(op.repeat.body) * op.repeat.times)
        else:
            flat.append(op)
    return flat


def _flat_work(round_: Round) -> list[int]:
    return [op.work for op in _flat(round_) if isinstance(op, Work)]
