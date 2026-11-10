"""Cas d’usage du plan de bonnet : hauteur, questions en attente (CLA-68, ADR 0020)."""

from decimal import Decimal

from knitproof.app.beanie import plan_beanie
from knitproof.domain.age import Age, AgeUnit
from knitproof.domain.beanie import BeanieReview, BeanieSpecification
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.gauge import GaugeSource
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.needle import (
    KnittingMethod,
    Needle,
    NeedleKind,
    NeedleSize,
    NeedleSystem,
)
from knitproof.domain.notice import NoticeCode, NoticeStatus
from knitproof.engine.verification import verify

THREE_YEARS = Age(value=3, unit=AgeUnit.YEARS)
RIBBING = StitchMultiple(repeat_multiple=4, repeat_offset=0)
DOUBLE_POINTED = Needle(
    size=NeedleSize(system=NeedleSystem.MM, original="4"), kind=NeedleKind.DOUBLE_POINTED
)


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def swatch(stitches: str, rows: str | None = "30") -> SwatchMeasurement:
    return SwatchMeasurement(
        stitches=Decimal(stitches),
        width=cm("10"),
        rows=None if rows is None else Decimal(rows),
        height=None if rows is None else cm("10"),
    )


def plan(
    *,
    age: Age | None = THREE_YEARS,
    total_height: str | None = "20",
    brim_height: str | None = "5",
    circumference: str = "43.2",
    after_blocking: SwatchMeasurement | None = None,
    worked: KnittingMethod = KnittingMethod.ROUND,
    source: GaugeSource = GaugeSource.BLOCKED,
) -> BeanieReview:
    spec = BeanieSpecification(
        age=age,
        total_height=None if total_height is None else cm(total_height),
        brim_height=None if brim_height is None else cm(brim_height),
        folded_brim=True,
        worked=worked,
        needles=(DOUBLE_POINTED,),
    )
    return plan_beanie(
        spec,
        circumference=cm(circumference),
        stitch_multiple=RIBBING,
        gauge=after_blocking or swatch("20"),
        source=source,
        before_blocking=swatch("22"),
    )


def codes(review: BeanieReview, status: NoticeStatus) -> list[NoticeCode]:
    return [n.code for n in review.notices if n.status is status]


def test_the_3_year_example_gives_88_stitches_and_17_crown_rounds() -> None:
    review = plan()

    assert review.plan is not None
    assert (review.plan.cast_on, review.plan.crown.round_count) == (88, 17)
    assert verify(review.plan.pattern) == []
    assert review.notices == ()
    assert review.questions == ()


def test_an_entered_height_wins_over_the_table() -> None:
    review = plan(age=Age(value=4, unit=AgeUnit.YEARS), total_height="20")

    assert review.plan is not None
    assert review.plan.finished_height == cm("20")
    assert review.notices == ()


def test_without_a_height_a_single_table_row_gives_a_warning_with_its_source() -> None:
    review = plan(age=Age(value=4, unit=AgeUnit.YEARS), total_height=None)

    assert review.plan is not None
    warning = next(n for n in review.notices if n.code is NoticeCode.HEIGHT_FROM_TABLE)
    assert warning.status is NoticeStatus.WARNING
    assert "À VÉRIFIER" in warning.text
    assert "Knit Picks" in warning.text
    assert review.plan.finished_height == Length(value=Decimal("8.5"), unit=LengthUnit.IN)


def test_an_age_without_a_table_row_needs_review() -> None:
    review = plan(age=Age(value=15, unit=AgeUnit.YEARS), total_height=None)

    assert review.plan is None
    assert codes(review, NoticeStatus.NEEDS_REVIEW) == [NoticeCode.HEIGHT_UNRESOLVED]
    assert [q.code for q in review.questions] == [NoticeCode.HEIGHT_UNRESOLVED]


def test_an_age_on_two_table_rows_needs_review_without_a_midpoint() -> None:
    review = plan(total_height=None)

    assert review.plan is None
    assert codes(review, NoticeStatus.NEEDS_REVIEW) == [NoticeCode.HEIGHT_UNRESOLVED]


def test_without_an_age_nor_a_height_the_question_is_asked() -> None:
    review = plan(age=None, total_height=None)

    assert review.plan is None
    assert [q.code for q in review.questions] == [NoticeCode.HEIGHT_UNRESOLVED]


def test_a_cast_on_under_32_stitches_needs_review_with_a_question() -> None:
    review = plan(circumference="15")

    assert review.plan is None
    assert codes(review, NoticeStatus.NEEDS_REVIEW) == [NoticeCode.CROWN_TOO_SMALL]
    assert [q.code for q in review.questions] == [NoticeCode.CROWN_TOO_SMALL]


def test_a_body_without_rows_needs_review_with_a_question() -> None:
    review = plan(total_height="10")

    assert review.plan is None
    assert codes(review, NoticeStatus.NEEDS_REVIEW) == [NoticeCode.BODY_TOO_SHORT]
    assert [q.code for q in review.questions] == [NoticeCode.BODY_TOO_SHORT]


def test_a_missing_brim_height_is_asked() -> None:
    review = plan(brim_height=None)

    assert review.plan is None
    assert [q.code for q in review.questions] == [NoticeCode.BRIM_HEIGHT_MISSING]


def test_a_missing_row_gauge_is_asked() -> None:
    review = plan(after_blocking=swatch("20", rows=None))

    assert review.plan is None
    assert [q.code for q in review.questions] == [NoticeCode.ROW_GAUGE_MISSING]


def test_the_row_gauge_question_names_the_blocked_swatch_by_default() -> None:
    review = plan(after_blocking=swatch("20", rows=None))

    assert "l’échantillon, après blocage" in review.questions[0].text


def test_the_row_gauge_question_names_the_unblocked_swatch() -> None:
    review = plan(after_blocking=swatch("20", rows=None), source=GaugeSource.UNBLOCKED)

    assert review.plan is None
    (question,) = review.questions
    assert question.code == NoticeCode.ROW_GAUGE_MISSING
    assert "avant blocage" in question.text
    assert "après blocage" not in question.text


def test_the_row_gauge_question_names_the_label() -> None:
    review = plan(after_blocking=swatch("20", rows=None), source=GaugeSource.LABEL)

    (question,) = review.questions
    assert "l’étiquette" in question.text
    assert "blocage" not in question.text


def test_every_missing_input_is_asked_at_once() -> None:
    review = plan(brim_height=None, after_blocking=swatch("20", rows=None))

    assert {q.code for q in review.questions} == {
        NoticeCode.BRIM_HEIGHT_MISSING,
        NoticeCode.ROW_GAUGE_MISSING,
    }


def test_a_flat_beanie_is_cast_on_with_its_selvedges() -> None:
    review = plan(worked=KnittingMethod.FLAT)

    assert review.plan is not None
    assert review.plan.cast_on == 90
    assert verify(review.plan.pattern) == []
