"""Propriétés du rang d’ajustement du bord au corps (CLA-103)."""

from hypothesis import example, given
from hypothesis import strategies as st

from knitproof.domain.pattern import Op, Pattern, Repeat, Round, Stitch, Work
from knitproof.domain.transition import Transition, TransitionRefusal, TransitionRejection
from knitproof.engine.transition import build_transition
from knitproof.engine.verification import simulate, verify

EDGES = st.integers(min_value=1, max_value=2000)
BODIES = st.integers(min_value=1, max_value=4000)


@st.composite
def feasible_pairs(draw: st.DrawFn) -> tuple[int, int]:
    edge = draw(EDGES)
    body = draw(st.integers(min_value=edge - edge // 2, max_value=2 * edge))
    return edge, body


def _flatten(ops: tuple[Op, ...]) -> list[Work | Stitch]:
    flat: list[Work | Stitch] = []
    for op in ops:
        if isinstance(op, Repeat):
            flat.extend(_flatten(op.repeat.body) * op.repeat.times)
        else:
            flat.append(op)
    return flat


def _sections(round_: Round) -> list[int]:
    """Mailles tricotées telles quelles avant chaque changement, dans l’ordre."""
    sizes: list[int] = []
    worked = 0
    for op in _flatten(round_.ops):
        if isinstance(op, Work):
            worked += op.work
        else:
            sizes.append(worked)
            worked = 0
    assert worked == 0
    return sizes


def _adjusted(edge: int, body: int) -> Round:
    transition = build_transition(edge, body)
    assert isinstance(transition, Transition)
    assert transition.adjustment_round is not None
    return transition.adjustment_round


@given(EDGES, BODIES)
@example(88, 44)
@example(88, 43)
@example(10, 20)
@example(10, 21)
@example(2, 1)
@example(3, 1)
def test_feasibility_is_exactly_the_physical_limits(edge: int, body: int) -> None:
    fewest, most = edge - edge // 2, 2 * edge
    result = build_transition(edge, body)

    if body < fewest:
        assert result == TransitionRefusal(
            edge_stitches=edge,
            body_stitches=body,
            reason=TransitionRejection.TOO_MANY_DECREASES,
            limit=fewest,
        )
    elif body > most:
        assert result == TransitionRefusal(
            edge_stitches=edge,
            body_stitches=body,
            reason=TransitionRejection.TOO_MANY_INCREASES,
            limit=most,
        )
    else:
        assert isinstance(result, Transition)


@given(feasible_pairs())
@example((88, 88))
@example((88, 44))
@example((10, 20))
def test_a_feasible_round_is_proved_by_the_engine(pair: tuple[int, int]) -> None:
    edge, body = pair
    transition = build_transition(edge, body)

    assert isinstance(transition, Transition)
    if edge == body:
        assert transition.adjustment_round is None
        return
    assert transition.adjustment_round is not None
    pattern = Pattern(cast_on=edge, rounds=(transition.adjustment_round,))
    assert verify(pattern) == []
    assert simulate(pattern).counts[-1].stitches == body


@given(feasible_pairs())
@example((88, 88))
def test_the_changes_are_all_in_the_right_direction(pair: tuple[int, int]) -> None:
    edge, body = pair
    if edge == body:
        assert _is_without_round(edge, body)
        return
    expected = Stitch.K2TOG if body < edge else Stitch.M1
    changes = [op for op in _flatten(_adjusted(edge, body).ops) if isinstance(op, Stitch)]

    assert changes == [expected] * abs(body - edge)


@given(feasible_pairs())
@example((88, 88))
@example((88, 81))
def test_the_sections_follow_the_rule_of_adr_0019(pair: tuple[int, int]) -> None:
    edge, body = pair
    if edge == body:
        assert _is_without_round(edge, body)
        return
    changes = abs(body - edge)
    worked = edge - 2 * changes if body < edge else edge
    quotient, remainder = divmod(worked, changes)
    sizes = _sections(_adjusted(edge, body))

    assert max(sizes) - min(sizes) <= 1
    assert sizes == [
        quotient + ((i + 1) * remainder // changes - i * remainder // changes)
        for i in range(changes)
    ]


@given(EDGES, BODIES)
def test_the_result_is_deterministic(edge: int, body: int) -> None:
    assert build_transition(edge, body) == build_transition(edge, body)


def _is_without_round(edge: int, body: int) -> bool:
    transition = build_transition(edge, body)
    return isinstance(transition, Transition) and transition.adjustment_round is None
