"""Question en attente et statut à revoir (CLA-68)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.notice import NoticeStatus
from knitproof.domain.question import PendingQuestion


def test_needs_review_is_a_notice_status() -> None:
    assert NoticeStatus.NEEDS_REVIEW.value == "needs_review"


def make() -> PendingQuestion:
    return PendingQuestion(
        code="folded_brim", text="Le bord est-il à revers ?", options=("oui", "non")
    )


def test_a_pending_question_is_frozen() -> None:
    with pytest.raises(ValidationError):
        make().text = "autre"  # type: ignore[misc]


def test_a_pending_question_forbids_extra_keys() -> None:
    with pytest.raises(ValidationError):
        PendingQuestion.model_validate({"code": "c", "text": "t", "options": (), "extra": 1})


@pytest.mark.parametrize("text", ["", "   "])
def test_a_pending_question_needs_a_text(text: str) -> None:
    with pytest.raises(ValidationError):
        PendingQuestion(code="c", text=text, options=())
