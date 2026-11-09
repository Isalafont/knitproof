"""Plan complet du bonnet : bord, corps et calotte en rangs entiers (CLA-68, ADR 0028).

Le bord et le corps gardent le même montage, sans transition (`build_transition` reste à part).
Les valeurs de la calotte et du magic loop viennent de `CrownRule` et `MagicLoopAdvice`,
lus par `app`.
"""

from decimal import Decimal

from knitproof.domain.beanie import (
    BeaniePlan,
    BeanieReview,
    KnittedRows,
    RowCount,
    RowRounding,
)
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.crown import Crown
from knitproof.domain.measure import DIVISION, EXACT, Length, SwatchMeasurement
from knitproof.domain.needle import KnittingMethod, Needle
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.pattern import Op, Pattern, Round, Work
from knitproof.domain.question import PendingQuestion
from knitproof.engine.cast_on import FLAT_SELVEDGES
from knitproof.engine.crown import crown_review
from knitproof.engine.height import knitted_rows
from knitproof.engine.needle_length import needle_change
from knitproof.engine.verification import verify

EVEN = 2

FLAT_DEPTH_TEXT = (
    "À VÉRIFIER : profondeur de calotte mesurée à plat, le tombé reste au tricot-test "
    "(ADR 0019, règle 9)"
)


def beanie_plan(
    *,
    stitches: int,
    worked: KnittingMethod,
    stitch_multiple: StitchMultiple,
    finished_height: Length,
    brim_height: Length,
    folded_brim: bool,
    after_blocking: SwatchMeasurement,
    before_blocking: SwatchMeasurement | None,
    needles: tuple[Needle, ...],
    crown_rule: CrownRule,
    advice: MagicLoopAdvice,
    precise_pattern: bool | None = None,
) -> BeanieReview:
    """Le bonnet en rangs ; `stitches` compte les mailles hors lisière.

    Les rangs viennent de la jauge après blocage. Sans plan possible (calotte trop petite,
    corps sans rang), la revue porte l’avis et la question, jamais un plan faux.
    """
    flat = worked is KnittingMethod.FLAT
    crown_result = crown_review(
        stitches,
        crown_rule,
        stitch_multiple=stitch_multiple.repeat_multiple,
        precise_pattern=precise_pattern,
        flat=flat,
    )
    crown = crown_result.crown
    if crown is None:
        return BeanieReview(
            plan=None, notices=crown_result.notices, questions=crown_result.questions
        )
    rows = knitted_rows(finished_height, brim_height, folded_brim, after_blocking)
    body = _body_rows(rows, crown, flat)
    if body is None:
        return _body_too_short(rows, crown, crown_result.notices, crown_result.questions)
    cast_on = stitches + FLAT_SELVEDGES if flat else stitches
    pattern = _pattern(cast_on, stitches, flat, rows.brim.rows, body.rows, crown)
    findings = verify(pattern)
    if findings:
        raise RuntimeError(f"plan de bonnet non vérifié : {findings}")
    plan = BeaniePlan(
        worked=worked,
        cast_on=cast_on,
        rows=rows,
        body=body,
        crown=crown,
        depth_cm=_depth_cm(crown, after_blocking),
        finished_height=finished_height,
        pattern=pattern,
    )
    notices = (
        *crown_result.notices,
        *_extra_notices(plan, needles, after_blocking, before_blocking, advice),
    )
    return BeanieReview(plan=plan, notices=notices, questions=crown_result.questions)


def _body_rows(rows: KnittedRows, crown: Crown, flat: bool) -> RowCount | None:
    """Le corps par différence de deux entiers ; à plat, réglé pour la parité (ADR 0028)."""
    body = rows.total.rows - rows.brim.rows - crown.round_count
    if body <= 0:
        return None
    raw = DIVISION.subtract(rows.total.raw, rows.brim.rows + crown.round_count)
    if not flat or (rows.brim.rows + body) % EVEN == 0:
        return RowCount(raw=raw, rows=body, rule=RowRounding.DIFFERENCE)
    candidates = [n for n in (body - 1, body + 1) if n > 0]
    adjusted = min(candidates, key=lambda n: (abs(DIVISION.subtract(n, raw)), n))
    return RowCount(raw=raw, rows=adjusted, rule=RowRounding.DIFFERENCE_FLAT_PARITY)


def _body_too_short(
    rows: KnittedRows,
    crown: Crown,
    notices: tuple[Notice, ...],
    questions: tuple[PendingQuestion, ...],
) -> BeanieReview:
    text = (
        f"À REVOIR : {rows.total.rows} rangs au total, dont {rows.brim.rows} de bord et "
        f"{crown.round_count} de calotte : il ne reste aucun rang pour le corps"
    )
    notice = Notice(status=NoticeStatus.NEEDS_REVIEW, code=NoticeCode.BODY_TOO_SHORT, text=text)
    question = PendingQuestion(
        code=NoticeCode.BODY_TOO_SHORT,
        text="La hauteur ne laisse aucun rang au corps : quelle hauteur ou quel bord retenir ?",
        options=(),
    )
    return BeanieReview(plan=None, notices=(*notices, notice), questions=(*questions, question))


def _pattern(
    cast_on: int, stitches: int, flat: bool, brim: int, body: int, crown: Crown
) -> Pattern:
    plain: tuple[Op, ...] = (Work(work=stitches),)
    if flat:
        plain = (Work(work=1), *plain, Work(work=1))
    offset = brim + body
    rounds = [
        Round(start=1, end=brim, ops=plain) if brim > 1 else Round(start=1, ops=plain),
        _plain_range(brim + 1, body, plain),
        *(_shifted(round_, offset) for round_ in crown.rounds),
    ]
    return Pattern(cast_on=cast_on, rounds=tuple(rounds))


def _plain_range(start: int, count: int, ops: tuple[Op, ...]) -> Round:
    if count == 1:
        return Round(start=start, ops=ops)
    return Round(start=start, end=start + count - 1, ops=ops)


def _shifted(round_: Round, offset: int) -> Round:
    end = None if round_.end is None else round_.end + offset
    return Round(
        start=round_.start + offset,
        end=end,
        ops=round_.ops,
        stated_count=round_.stated_count,
    )


def _depth_cm(crown: Crown, swatch: SwatchMeasurement) -> Decimal:
    """Rangs de la calotte, fois la hauteur de l’échantillon, sur ses rangs (ADR 0019, règle 9)."""
    if swatch.rows is None or swatch.height is None:
        raise ValueError("la jauge en rangs est absente de l’échantillon")
    return DIVISION.divide(EXACT.multiply(crown.round_count, swatch.height.in_cm), swatch.rows)


def _extra_notices(
    plan: BeaniePlan,
    needles: tuple[Needle, ...],
    after_blocking: SwatchMeasurement,
    before_blocking: SwatchMeasurement | None,
    advice: MagicLoopAdvice,
) -> tuple[Notice, ...]:
    if plan.worked is KnittingMethod.FLAT:
        flat = Notice(
            status=NoticeStatus.WARNING, code=NoticeCode.CROWN_DEPTH_FLAT, text=FLAT_DEPTH_TEXT
        )
        return (flat,)
    offset = plan.rows.brim.rows + plan.body.rows
    change = needle_change(plan.crown, needles[-1], after_blocking, before_blocking, advice)
    if change is None:
        return ()
    if change.round is not None:
        change = change.model_copy(update={"round": change.round + offset})
    return (change,)
