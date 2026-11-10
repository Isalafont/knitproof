"""Plan complet du bonnet : bord, corps, calotte (CLA-68, ADR 0028)."""

import datetime
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.beanie import BeanieReview, RowRounding
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.needle import (
    KnittingMethod,
    Needle,
    NeedleKind,
    NeedleSize,
    NeedleSystem,
)
from knitproof.domain.notice import NoticeCode, NoticeStatus
from knitproof.domain.provenance import SourceKind
from knitproof.engine.beanie import beanie_plan
from knitproof.engine.verification import verify

SOURCE = {
    "kind": SourceKind.PERSON_DECISION,
    "reference": "Isabelle, ADR 0019",
    "read_on": datetime.date(2026, 11, 2),
}
RULE = CrownRule.model_validate(
    {
        "id": "calotte",
        "source": SOURCE,
        "decreases_per_round": 8,
        "last_round_below": 24,
        "min_cast_on": 32,
        "every_round_last": 3,
    }
)
ADVICE = MagicLoopAdvice.model_validate(
    {
        "id": "magic-loop-cable",
        "magic_loop_cable": {"value": "80", "unit": "cm"},
        "source": {
            "kind": SourceKind.REFERENCE_MEASUREMENT,
            "reference": "ADR 0023 §6",
            "read_on": datetime.date(2026, 11, 2),
        },
    }
)
RIBBING = StitchMultiple(repeat_multiple=4, repeat_offset=0)
AFTER = SwatchMeasurement(
    stitches=Decimal(20),
    width=Length(value=Decimal(10), unit=LengthUnit.CM),
    rows=Decimal(30),
    height=Length(value=Decimal(10), unit=LengthUnit.CM),
)
BEFORE = SwatchMeasurement(
    stitches=Decimal(22),
    width=Length(value=Decimal(10), unit=LengthUnit.CM),
    rows=Decimal(30),
    height=Length(value=Decimal(10), unit=LengthUnit.CM),
)


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def circular(length: str | None) -> Needle:
    cable = None if length is None else cm(length)
    return Needle(
        size=NeedleSize(system=NeedleSystem.MM, original="4"),
        kind=NeedleKind.CIRCULAR,
        cable_length=cable,
    )


def review_for(
    *,
    finished: str = "20",
    brim: str = "5",
    folded: bool = True,
    worked: KnittingMethod = KnittingMethod.ROUND,
    needle: Needle | None = None,
    before: SwatchMeasurement | None = None,
    stitches: int = 88,
) -> BeanieReview:
    return beanie_plan(
        stitches=stitches,
        worked=worked,
        stitch_multiple=RIBBING,
        finished_height=cm(finished),
        brim_height=cm(brim),
        folded_brim=folded,
        after_blocking=AFTER,
        before_blocking=before,
        needles=(needle or circular(None),),
        crown_rule=RULE,
        advice=ADVICE,
    )


def test_the_3_year_example_gives_a_brim_of_30_a_body_of_28_and_a_crown_of_17() -> None:
    plan = review_for().plan

    assert plan is not None
    assert (plan.rows.brim.rows, plan.body.rows, plan.crown.round_count) == (30, 28, 17)
    assert plan.rows.total.rows == 75
    assert plan.finished_height == cm("20")
    assert plan.body.rule is RowRounding.DIFFERENCE


def test_the_crown_depth_follows_from_its_rounds() -> None:
    plan = review_for().plan

    assert plan is not None
    assert plan.depth_cm.quantize(Decimal("0.01")) == Decimal("5.67")


def test_the_whole_pattern_passes_verification() -> None:
    plan = review_for().plan

    assert plan is not None
    assert plan.pattern.cast_on == 88
    assert verify(plan.pattern) == []
    assert plan.pattern.rounds[-1].last == 75


def test_a_body_of_zero_rows_needs_review_without_a_plan() -> None:
    review = review_for(finished="10", brim="5")

    assert review.plan is None
    assert [(n.status, n.code) for n in review.notices] == [
        (NoticeStatus.NEEDS_REVIEW, NoticeCode.BODY_TOO_SHORT)
    ]
    assert [q.code for q in review.questions] == [NoticeCode.BODY_TOO_SHORT]


def test_a_flat_plan_casts_on_the_selvedges_too() -> None:
    plan = review_for(worked=KnittingMethod.FLAT).plan

    assert plan is not None
    assert plan.pattern.cast_on == 90
    assert verify(plan.pattern) == []


def test_a_flat_plan_starts_its_crown_on_a_right_side_row() -> None:
    plan = review_for(worked=KnittingMethod.FLAT, finished="21").plan

    assert plan is not None
    assert (plan.rows.brim.rows + plan.body.rows) % 2 == 0
    assert plan.body.rule is RowRounding.DIFFERENCE_FLAT_PARITY
    assert plan.body.rows == 28


def test_a_flat_plan_adjusts_its_body_to_the_nearest_of_the_raw_count() -> None:
    plan = review_for(worked=KnittingMethod.FLAT, finished="20.4").plan

    assert plan is not None
    assert plan.body.raw == Decimal("27.2")
    assert plan.body.rows == 28


def test_a_flat_plan_already_on_the_right_side_keeps_its_body() -> None:
    plan = review_for(worked=KnittingMethod.FLAT).plan

    assert plan is not None
    assert (plan.crown.round_count, plan.body.rows) == (19, 26)
    assert plan.body.rule is RowRounding.DIFFERENCE


def test_a_flat_plan_marks_its_crown_depth_to_verify() -> None:
    review = review_for(worked=KnittingMethod.FLAT)

    codes = [(n.status, n.code) for n in review.notices]
    assert (NoticeStatus.WARNING, NoticeCode.CROWN_DEPTH_FLAT) in codes
    assert "À VÉRIFIER" in next(
        n.text for n in review.notices if n.code is NoticeCode.CROWN_DEPTH_FLAT
    )


def test_a_round_plan_has_no_flat_depth_notice() -> None:
    review = review_for()

    assert all(n.code is not NoticeCode.CROWN_DEPTH_FLAT for n in review.notices)


def test_a_circular_needle_changes_inside_the_crown_of_the_full_plan() -> None:
    review = review_for(needle=circular("40"), before=BEFORE)

    notices = [n for n in review.notices if n.code is NoticeCode.NEEDLE_CHANGE]
    assert [n.round for n in notices] == [60]


def test_a_flat_plan_never_changes_needles() -> None:
    review = review_for(worked=KnittingMethod.FLAT, needle=circular("40"), before=BEFORE)

    assert all(n.code is not NoticeCode.NEEDLE_CHANGE for n in review.notices)


@given(finished=st.integers(min_value=12, max_value=60))
def test_a_flat_plan_always_has_its_crown_on_the_right_side(finished: int) -> None:
    plan = review_for(worked=KnittingMethod.FLAT, finished=str(finished)).plan

    assert plan is not None
    assert (plan.rows.brim.rows + plan.body.rows) % 2 == 0
    assert verify(plan.pattern) == []
    assert abs(plan.body.rows - plan.body.raw) <= Decimal("1.5")
