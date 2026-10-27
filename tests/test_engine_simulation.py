"""`simulate` : comptes tour par tour et arrêt sur une répétition fausse (CLA-64)."""

from knitproof.domain.finding import FindingCode, FindingStatus
from knitproof.domain.location import SourceLocation
from knitproof.domain.pattern import Pattern, Repeat, RepeatBlock, Round, Stitch, Work
from knitproof.engine.verification import simulate


def _decrease_repeat(work: int, times: int) -> Repeat:
    return Repeat(repeat=RepeatBlock(body=(Work(work=work), Stitch.K2TOG), times=times))


def test_fitting_pattern_gets_one_count_per_round() -> None:
    pattern = Pattern(
        cast_on=108,
        rounds=(
            Round(start=1, end=30, ops=(Work(work=108),)),
            Round(start=31, ops=(_decrease_repeat(10, 9),)),
        ),
    )

    simulation = simulate(pattern)

    assert len(simulation.counts) == 31
    assert simulation.counts[-1].round == 31
    assert simulation.counts[-1].stitches == 99
    assert simulation.halted is None


def test_repeat_not_fitting_halts_the_simulation() -> None:
    pattern = Pattern(
        cast_on=100,
        rounds=(
            Round(start=1, ops=(_decrease_repeat(10, 9),)),
            Round(start=2, ops=(Work(work=91),)),
        ),
    )

    simulation = simulate(pattern)

    assert simulation.counts == ()
    assert simulation.halted is not None
    assert simulation.halted.status is FindingStatus.ERROR
    assert simulation.halted.code is FindingCode.REPEAT_NOT_FITTING
    assert simulation.halted.round == 1
    assert simulation.halted.expected == 100
    assert simulation.halted.actual == 108


def test_range_of_rounds_repeats_the_same_operations() -> None:
    pattern = Pattern(
        cast_on=10,
        rounds=(Round(start=1, end=3, ops=(Work(work=10), Stitch.M1)),),
    )

    simulation = simulate(pattern)

    assert [count.stitches for count in simulation.counts] == [11]
    assert simulation.halted is not None
    assert simulation.halted.code is FindingCode.REPEAT_NOT_FITTING
    assert simulation.halted.round == 2


def test_halting_round_location_is_copied_into_the_finding() -> None:
    location = SourceLocation(page=3, line=8)
    pattern = Pattern(
        cast_on=10,
        rounds=(Round(start=1, ops=(Work(work=12),), location=location),),
    )

    simulation = simulate(pattern)

    assert simulation.halted is not None
    assert simulation.halted.location == location
