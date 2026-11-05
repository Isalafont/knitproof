"""Rang d’ajustement du bord au corps (CLA-103)."""

from decimal import Decimal

import pytest

from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.pattern import Op, Pattern, Round
from knitproof.domain.transition import Transition, TransitionRefusal, TransitionRejection
from knitproof.engine.cast_on import cast_on
from knitproof.engine.transition import build_transition
from knitproof.engine.verification import verify


def _ops(*raw: object) -> tuple[Op, ...]:
    return Round.model_validate({"start": 1, "ops": raw}).ops


def _repeat(times: int, *body: object) -> dict[str, object]:
    return {"repeat": {"body": body, "times": times}}


def _transition(edge: int, body: int) -> Transition:
    result = build_transition(edge, body)
    assert isinstance(result, Transition)
    return result


def _round(edge: int, body: int) -> Round:
    round_ = _transition(edge, body).adjustment_round
    assert round_ is not None
    return round_


def _refusal(edge: int, body: int) -> TransitionRefusal:
    result = build_transition(edge, body)
    assert isinstance(result, TransitionRefusal)
    return result


def test_readme_cast_ons_give_the_edge_and_the_body_of_the_ticket() -> None:
    target = Length(value=Decimal("43.2"), unit=LengthUnit.CM)
    swatch = SwatchMeasurement(
        stitches=Decimal(20), width=Length(value=Decimal(10), unit=LengthUnit.CM)
    )

    edge = cast_on(target, swatch, StitchMultiple(repeat_multiple=4, repeat_offset=0))
    body = cast_on(target, swatch, StitchMultiple(repeat_multiple=6, repeat_offset=0))

    assert (edge.stitches, body.stitches) == (88, 84)
    assert _round(edge.stitches, body.stitches).ops == _ops(_repeat(4, {"work": 20}, "k2tog"))
    pattern = Pattern(cast_on=88, rounds=(_round(88, 84),))
    assert verify(pattern) == []


def test_decrease_from_a_rib_edge() -> None:
    assert _round(96, 88).ops == _ops(_repeat(8, {"work": 10}, "k2tog"))


def test_irregular_decrease_spreads_the_remainder() -> None:
    assert _round(88, 81).ops == _ops(
        {"work": 10},
        "k2tog",
        {"work": 11},
        "k2tog",
        {"work": 10},
        "k2tog",
        {"work": 11},
        "k2tog",
        {"work": 10},
        "k2tog",
        _repeat(2, {"work": 11}, "k2tog"),
    )
    assert verify(Pattern(cast_on=88, rounds=(_round(88, 81),))) == []


def test_increase() -> None:
    assert _round(84, 88).ops == _ops(_repeat(4, {"work": 21}, "m1"))
    assert verify(Pattern(cast_on=84, rounds=(_round(84, 88),))) == []


@pytest.mark.parametrize(
    ("edge", "body", "expected"),
    [
        (88, 44, (_repeat(44, "k2tog"),)),
        (10, 20, (_repeat(10, {"work": 1}, "m1"),)),
        (2, 1, ("k2tog",)),
        (1, 2, ({"work": 1}, "m1")),
    ],
)
def test_limits_are_reachable(edge: int, body: int, expected: tuple[object, ...]) -> None:
    assert _round(edge, body).ops == _ops(*expected)
    assert verify(Pattern(cast_on=edge, rounds=(_round(edge, body),))) == []


@pytest.mark.parametrize(
    ("edge", "body", "reason", "limit"),
    [
        (88, 43, TransitionRejection.TOO_MANY_DECREASES, 44),
        (3, 1, TransitionRejection.TOO_MANY_DECREASES, 2),
        (10, 21, TransitionRejection.TOO_MANY_INCREASES, 20),
    ],
)
def test_a_gap_beyond_one_round_is_refused(
    edge: int, body: int, reason: TransitionRejection, limit: int
) -> None:
    refusal = _refusal(edge, body)

    assert (refusal.edge_stitches, refusal.body_stitches) == (edge, body)
    assert (refusal.reason, refusal.limit) == (reason, limit)


def test_equal_counts_need_no_round() -> None:
    transition = _transition(88, 88)

    assert transition.adjustment_round is None
