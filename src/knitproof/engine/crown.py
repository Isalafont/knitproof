"""Calotte en rond : diminutions réparties, rythme et dernier rang (CLA-68, ADR 0019).

Les seuils viennent de `CrownRule`, lu par `app` et passé ici.
"""

from itertools import groupby

from knitproof.domain.construction import CrownRule
from knitproof.domain.crown import Crown, CrownReview
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.pattern import Op, Repeat, RepeatBlock, Round, Stitch, Work
from knitproof.domain.question import PendingQuestion
from knitproof.engine.cast_on import FLAT_SELVEDGES

EVERY_OTHER_ROUND = 2
FLAT_EVERY_ROUND_LAST = 1  # à plat, seul le dernier rang diminue hors rythme (ADR 0028)


LONE_STITCH_WARNING = (
    "montage impair : une maille seule reste au dernier rang, à l’endroit"  # ADR 0019, règle 5
)


def crown_review(
    stitches: int,
    rule: CrownRule,
    *,
    stitch_multiple: int | None = None,
    precise_pattern: bool | None = None,
    flat: bool = False,
) -> CrownReview:
    """La calotte avec ses avis (ADR 0019, règles 5 à 8).

    `precise_pattern` dit si le point est marqué « motif précis » ; `None` quand la marque
    n’existe pas encore : un compte impair est alors à revoir (règle 7).
    """
    if stitches < rule.min_cast_on:
        return _too_small(stitches, rule)
    crown = crown_plan(stitches, rule, flat=flat)
    if stitches % Stitch.K2TOG.consumes == 0:
        return CrownReview(crown=crown)
    if precise_pattern is None or precise_pattern:
        return _odd_needs_review(crown)
    if stitch_multiple == 1:
        notice = Notice(
            status=NoticeStatus.WARNING,
            code=NoticeCode.CROWN_LONE_STITCH,
            text=LONE_STITCH_WARNING,
        )
        return CrownReview(crown=crown, notices=(notice,))
    return CrownReview(crown=crown)


def crown_plan(stitches: int, rule: CrownRule, *, flat: bool = False) -> Crown:
    """La calotte d’un montage ; refusée sous le minimum de `rule` (ADR 0019, règle 8).

    À plat, `stitches` compte les mailles hors lisière : les diminutions se font à l’endroit,
    un rang sur deux, et chaque rang est encadré de ses lisières (ADR 0028).
    """
    if stitches < rule.min_cast_on:
        raise ValueError(f"montage de {stitches} m sous le minimum de {rule.min_cast_on} m")
    regular = _regular_decrease_rounds(stitches, rule)
    decrease_rounds = regular + 1
    every_round_last = FLAT_EVERY_ROUND_LAST if flat else rule.every_round_last
    total = EVERY_OTHER_ROUND * decrease_rounds - every_round_last
    rounds: list[Round] = []
    count = stitches
    for number in range(1, total + 1):
        if number == total:
            round_, count = _last_round(number, count)
        elif number % EVERY_OTHER_ROUND == 1 or number > total - every_round_last:
            round_, count = _decrease_round(number, count, rule.decreases_per_round)
        else:
            round_ = Round(start=number, ops=(Work(work=count),))
        rounds.append(_with_selvedges(round_) if flat else round_)
    return Crown(
        stitches=stitches, rounds=tuple(rounds), decrease_rounds=decrease_rounds, remaining=count
    )


def _with_selvedges(round_: Round) -> Round:
    """La maille glissée en tête et la maille de fin, comptées comme travaillées."""
    stated = None if round_.stated_count is None else round_.stated_count + FLAT_SELVEDGES
    ops = (Work(work=1), *round_.ops, Work(work=1))
    return Round(start=round_.start, ops=ops, stated_count=stated)


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


def _too_small(stitches: int, rule: CrownRule) -> CrownReview:
    text = (
        f"À REVOIR : montage de {stitches} m, sous le minimum de {rule.min_cast_on} m "
        "pour une calotte de bonnet (ADR 0019, règle 8)"
    )
    notice = Notice(status=NoticeStatus.NEEDS_REVIEW, code=NoticeCode.CROWN_TOO_SMALL, text=text)
    question = PendingQuestion(
        code=NoticeCode.CROWN_TOO_SMALL,
        text=f"Le montage de {stitches} m est trop petit pour la calotte : que faire ?",
        options=(),
    )
    return CrownReview(crown=None, notices=(notice,), questions=(question,))


def _odd_needs_review(crown: Crown) -> CrownReview:
    text = (
        f"À REVOIR : montage de {crown.stitches} m, impair : une maille seule reste au dernier "
        "rang (ADR 0019, règles 6 et 7)"
    )
    notice = Notice(status=NoticeStatus.NEEDS_REVIEW, code=NoticeCode.CROWN_ODD_STITCHES, text=text)
    question = PendingQuestion(
        code=NoticeCode.CROWN_ODD_STITCHES,
        text="Le montage est impair : le point a-t-il un motif précis ?",
        options=("oui", "non"),
    )
    return CrownReview(crown=crown, notices=(notice,), questions=(question,))
