"""Calotte en rond : diminutions réparties, rythme et dernier rang (CLA-68, ADR 0019).

Les seuils viennent de `CrownRule`, lu par `app` et passé ici.
"""

from itertools import groupby

from knitproof.domain.construction import CrownRule
from knitproof.domain.crown import Crown
from knitproof.domain.pattern import Op, Repeat, RepeatBlock, Round, Stitch, Work

EVERY_OTHER_ROUND = 2


def crown_plan(stitches: int, rule: CrownRule) -> Crown:
    """La calotte d’un montage ; refusée sous le minimum de `rule` (ADR 0019, règle 8)."""
    if stitches < rule.min_cast_on:
        raise ValueError(f"montage de {stitches} m sous le minimum de {rule.min_cast_on} m")
    regular = _regular_decrease_rounds(stitches, rule)
    decrease_rounds = regular + 1
    total = EVERY_OTHER_ROUND * decrease_rounds - rule.every_round_last
    rounds: list[Round] = []
    count = stitches
    for number in range(1, total + 1):
        if number == total:
            round_, count = _last_round(number, count)
        elif number % EVERY_OTHER_ROUND == 1 or number > total - rule.every_round_last:
            round_, count = _decrease_round(number, count, rule.decreases_per_round)
        else:
            round_ = Round(start=number, ops=(Work(work=count),))
        rounds.append(round_)
    return Crown(
        stitches=stitches, rounds=tuple(rounds), decrease_rounds=decrease_rounds, remaining=count
    )


def _regular_decrease_rounds(stitches: int, rule: CrownRule) -> int:
    count, rounds = stitches, 0
    while count >= rule.last_round_below:
        count -= rule.decreases_per_round
        rounds += 1
    return rounds


def _decrease_round(number: int, count: int, sections: int) -> tuple[Round, int]:
    remainder = count % sections
    sizes = [
        count // sections + (i + 1) * remainder // sections - i * remainder // sections
        for i in range(sections)
    ]
    after = count - sections
    round_ = Round(start=number, ops=_compact(sizes), stated_count=after)
    return round_, after


def _last_round(number: int, count: int) -> tuple[Round, int]:
    pairs = count // Stitch.K2TOG.consumes
    ops: list[Op] = [Repeat(repeat=RepeatBlock(body=(Stitch.K2TOG,), times=pairs))]
    alone = count % Stitch.K2TOG.consumes
    if alone:
        ops.append(Work(work=alone))
    after = pairs + alone
    return Round(start=number, ops=tuple(ops), stated_count=after), after


def _compact(sizes: list[int]) -> tuple[Op, ...]:
    ops: list[Op] = []
    for size, group in groupby(sizes):
        worked = size - Stitch.K2TOG.consumes
        section: tuple[Op, ...] = (Work(work=worked), Stitch.K2TOG)
        times = len(list(group))
        if times > 1:
            ops.append(Repeat(repeat=RepeatBlock(body=section, times=times)))
        else:
            ops.extend(section)
    return tuple(ops)
