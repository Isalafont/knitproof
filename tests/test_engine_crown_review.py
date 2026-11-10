"""Cas limites de la calotte : compte impair, montage trop petit (CLA-68, ADR 0019)."""

import datetime

from knitproof.domain.construction import CrownRule
from knitproof.domain.notice import NoticeCode, NoticeStatus
from knitproof.domain.provenance import SourceKind
from knitproof.engine.crown import crown_review

RULE = CrownRule.model_validate(
    {
        "id": "calotte",
        "source": {
            "kind": SourceKind.PERSON_DECISION,
            "reference": "Isabelle, ADR 0019",
            "read_on": datetime.date(2026, 11, 2),
        },
        "decreases_per_round": 8,
        "last_round_below": 24,
        "min_cast_on": 32,
        "every_round_last": 3,
    }
)


def test_an_even_count_has_no_notice_and_no_question() -> None:
    review = crown_review(88, RULE)

    assert review.crown is not None
    assert review.notices == ()
    assert review.questions == ()


def test_an_odd_count_needs_review_with_a_question_and_the_plan_goes_on() -> None:
    review = crown_review(91, RULE)

    assert review.crown is not None
    assert review.crown.remaining == 10
    assert [(n.status, n.code) for n in review.notices] == [
        (NoticeStatus.NEEDS_REVIEW, NoticeCode.CROWN_ODD_STITCHES)
    ]
    assert [q.code for q in review.questions] == ["crown_odd_stitches"]


def test_a_crown_below_the_minimum_needs_review_without_a_crown() -> None:
    review = crown_review(31, RULE)

    assert review.crown is None
    assert [(n.status, n.code) for n in review.notices] == [
        (NoticeStatus.NEEDS_REVIEW, NoticeCode.CROWN_TOO_SMALL)
    ]
    assert [q.code for q in review.questions] == ["crown_too_small"]


def test_the_minimum_itself_is_accepted() -> None:
    assert crown_review(32, RULE).crown is not None


def test_the_lone_stitch_warning_is_not_raised_without_the_pattern_mark() -> None:
    review = crown_review(91, RULE, stitch_multiple=1)

    assert NoticeCode.CROWN_LONE_STITCH not in [n.code for n in review.notices]


def test_the_lone_stitch_warning_is_raised_for_an_unmarked_pattern_of_multiple_1() -> None:
    review = crown_review(91, RULE, stitch_multiple=1, precise_pattern=False)

    assert [(n.status, n.code) for n in review.notices] == [
        (NoticeStatus.WARNING, NoticeCode.CROWN_LONE_STITCH)
    ]
    assert review.questions == ()


def test_an_unmarked_pattern_of_multiple_2_explains_the_odd_count() -> None:
    review = crown_review(91, RULE, stitch_multiple=2, precise_pattern=False)

    assert review.notices == ()


def test_a_precise_pattern_needs_review_whatever_the_multiple() -> None:
    review = crown_review(91, RULE, stitch_multiple=2, precise_pattern=True)

    assert [n.code for n in review.notices] == [NoticeCode.CROWN_ODD_STITCHES]
