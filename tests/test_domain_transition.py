"""Invariants de la transition du bord au corps (CLA-103)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.pattern import Round
from knitproof.domain.transition import Transition


def _round(**overrides: object) -> Round:
    raw: dict[str, object] = {"start": 1, "ops": ({"work": 2}, "k2tog"), "stated_count": 3}
    return Round.model_validate({**raw, **overrides})


def test_equal_counts_without_a_round_are_accepted() -> None:
    transition = Transition(edge_stitches=88, body_stitches=88, adjustment_round=None)

    assert transition.adjustment_round is None


def test_a_round_that_bridges_the_edge_to_the_body_is_accepted() -> None:
    transition = Transition(edge_stitches=4, body_stitches=3, adjustment_round=_round())

    assert transition.adjustment_round == _round()


def test_different_counts_without_a_round_are_refused() -> None:
    with pytest.raises(ValidationError, match="requis"):
        Transition(edge_stitches=4, body_stitches=3, adjustment_round=None)


def test_a_round_with_equal_counts_is_refused() -> None:
    with pytest.raises(ValidationError, match="égaux"):
        Transition(edge_stitches=3, body_stitches=3, adjustment_round=_round(ops=({"work": 3},)))


def test_a_round_that_does_not_consume_the_edge_is_refused() -> None:
    with pytest.raises(ValidationError, match="consommer le bord"):
        Transition(edge_stitches=5, body_stitches=3, adjustment_round=_round())


@pytest.mark.parametrize("stated", [None, 4])
def test_a_missing_or_wrong_stated_count_is_refused(stated: int | None) -> None:
    with pytest.raises(ValidationError, match="produire le corps"):
        Transition(edge_stitches=4, body_stitches=3, adjustment_round=_round(stated_count=stated))


@pytest.mark.parametrize("overrides", [{"end": 2}, {"start": 2}])
def test_a_round_range_or_a_start_other_than_one_is_refused(overrides: dict[str, int]) -> None:
    with pytest.raises(ValidationError, match="rang 1"):
        Transition(edge_stitches=4, body_stitches=3, adjustment_round=_round(**overrides))


def test_a_bool_is_refused_as_a_count() -> None:
    with pytest.raises(ValidationError):
        Transition.model_validate(
            {"edge_stitches": True, "body_stitches": 1, "adjustment_round": None}
        )
