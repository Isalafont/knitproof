"""Simulation des comptes de mailles d’un patron."""

from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.pattern import Pattern
from knitproof.domain.simulation import RoundCount, Simulation


def verify(pattern: Pattern) -> list[Finding]:
    """Constats d’un patron : comptes annoncés faux, puis répétition qui ne tombe pas juste."""
    simulation = simulate(pattern)
    simulated = {count.round: count.stitches for count in simulation.counts}
    findings: list[Finding] = []
    for round_ in pattern.rounds:
        expected = simulated.get(round_.last)
        if expected is None or round_.stated_count in (None, expected):
            continue
        findings.append(
            Finding(
                status=FindingStatus.ERROR,
                code=FindingCode.COUNT_MISMATCH,
                round=round_.last,
                expected=expected,
                actual=round_.stated_count,
                location=round_.location,
            )
        )
    if simulation.halted is not None:
        findings.append(simulation.halted)
    return findings


def simulate(pattern: Pattern) -> Simulation:
    """Compte les mailles tour par tour, jusqu’au premier tour qui ne tombe pas juste."""
    stitches = pattern.cast_on
    counts: list[RoundCount] = []
    for round_ in pattern.rounds:
        for number in range(round_.start, round_.last + 1):
            if round_.consumes != stitches:
                halted = Finding(
                    status=FindingStatus.ERROR,
                    code=FindingCode.REPEAT_NOT_FITTING,
                    round=number,
                    expected=stitches,
                    actual=round_.consumes,
                    location=round_.location,
                )
                return Simulation(counts=tuple(counts), halted=halted)
            stitches = round_.produces
            counts.append(RoundCount(round=number, stitches=stitches))
    return Simulation(counts=tuple(counts))
