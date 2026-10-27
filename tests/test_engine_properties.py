"""Invariants de la simulation sur des patrons justes tirés au hasard (CLA-64)."""

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.finding import FindingCode
from knitproof.domain.pattern import Op, Pattern, Round, Stitch, Work
from knitproof.engine.verification import simulate, verify

MAX_CAST_ON = 200
MAX_ROUNDS = 10
MAX_INCREASES = 5


@st.composite
def fitting_patterns(draw: st.DrawFn) -> Pattern:
    stitches = draw(st.integers(min_value=1, max_value=MAX_CAST_ON))
    cast_on = stitches
    rounds: list[Round] = []
    for number in range(1, draw(st.integers(min_value=1, max_value=MAX_ROUNDS)) + 1):
        decreases = draw(st.integers(min_value=0, max_value=stitches // 2))
        increases = draw(st.integers(min_value=0, max_value=MAX_INCREASES))
        plain = stitches - 2 * decreases
        ops: list[Op] = [*[Stitch.K2TOG] * decreases, *[Stitch.M1] * increases]
        if plain > 0:
            ops.append(Work(work=plain))
        shuffled = draw(st.permutations(ops))
        stitches = stitches - decreases + increases
        stated = draw(st.sampled_from([None, stitches]))
        rounds.append(Round(start=number, ops=tuple(shuffled), stated_count=stated))
    return Pattern(cast_on=cast_on, rounds=tuple(rounds))


@given(fitting_patterns())
def test_fitting_pattern_has_no_finding_and_one_count_per_round(pattern: Pattern) -> None:
    assert verify(pattern) == []
    assert len(simulate(pattern).counts) == len(pattern.rounds)


@given(fitting_patterns())
def test_each_round_produces_consumed_minus_k2tog_plus_m1(pattern: Pattern) -> None:
    counts = simulate(pattern).counts

    for round_, count in zip(pattern.rounds, counts, strict=True):
        decreases = round_.ops.count(Stitch.K2TOG)
        increases = round_.ops.count(Stitch.M1)
        assert count.stitches == round_.consumes - decreases + increases


@given(fitting_patterns(), st.data())
def test_shifted_stated_count_gives_exactly_one_mismatch(
    pattern: Pattern, data: st.DataObject
) -> None:
    index = data.draw(st.integers(min_value=0, max_value=len(pattern.rounds) - 1))
    simulated = simulate(pattern).counts[index].stitches
    shifted = data.draw(
        st.integers(min_value=0, max_value=2 * simulated + 1).filter(lambda v: v != simulated)
    )
    rounds = list(pattern.rounds)
    rounds[index] = rounds[index].model_copy(update={"stated_count": shifted})

    findings = verify(Pattern(cast_on=pattern.cast_on, rounds=tuple(rounds)))

    assert len(findings) == 1
    assert findings[0].code is FindingCode.COUNT_MISMATCH
    assert findings[0].round == index + 1
    assert findings[0].expected == simulated
    assert findings[0].actual == shifted


@given(fitting_patterns(), st.data())
def test_extra_work_halts_the_simulation_at_that_round(
    pattern: Pattern, data: st.DataObject
) -> None:
    index = data.draw(st.integers(min_value=0, max_value=len(pattern.rounds) - 1))
    extra = data.draw(st.integers(min_value=1, max_value=MAX_CAST_ON))
    rounds = list(pattern.rounds)
    broken = rounds[index]
    rounds[index] = broken.model_copy(update={"ops": (Work(work=extra), *broken.ops)})

    simulation = simulate(Pattern(cast_on=pattern.cast_on, rounds=tuple(rounds)))

    assert simulation.halted is not None
    assert simulation.halted.code is FindingCode.REPEAT_NOT_FITTING
    assert simulation.halted.round == index + 1
    assert len(simulation.counts) == index
