"""`Report` et `ReportEntry` : le rapport unique du moteur (CLA-69, ADR 0029)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.question import PendingQuestion
from knitproof.domain.report import DecidedBy, Report, ReportEntry, ReportStatus


def _entry(status: ReportStatus, decided_by: DecidedBy = DecidedBy.ENGINE) -> ReportEntry:
    return ReportEntry(
        status=status,
        code="count_mismatch",
        round=33,
        lines=("Annoncé : 89 m · Calculé : 90 m",),
        decided_by=decided_by,
    )


def test_an_entry_is_frozen_and_forbids_extra_fields() -> None:
    entry = _entry(ReportStatus.ERROR)

    with pytest.raises(ValidationError):
        entry.code = "autre"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ReportEntry(
            status=ReportStatus.ERROR,
            code="x",
            round=None,
            lines=(),
            decided_by=DecidedBy.ENGINE,
            extra=1,  # type: ignore[call-arg]
        )


def test_statuses_and_deciders() -> None:
    assert {status.value for status in ReportStatus} == {
        "error",
        "warning",
        "needs_review",
        "rejected",
    }
    assert {decided.value for decided in DecidedBy} == {"engine", "entered", "library"}


def test_decided_by_engine_reads_as_a_verifiable_calculation() -> None:
    assert DecidedBy.ENGINE.label == "le moteur (calcul vérifiable)"


def test_an_empty_report_has_no_errors_and_nothing_to_review() -> None:
    report = Report(entries=(), questions=())

    assert not report.has_errors
    assert not report.needs_review
    assert report.result is None


def test_has_errors_counts_errors_only() -> None:
    assert Report(entries=(_entry(ReportStatus.ERROR),), questions=()).has_errors
    assert not Report(entries=(_entry(ReportStatus.WARNING),), questions=()).has_errors


def test_needs_review_follows_an_entry_or_a_question() -> None:
    question = PendingQuestion(code="row_gauge", text="Quelle jauge ?", options=())

    assert Report(entries=(_entry(ReportStatus.NEEDS_REVIEW),), questions=()).needs_review
    assert Report(entries=(), questions=(question,)).needs_review
    assert not Report(entries=(_entry(ReportStatus.REJECTED),), questions=()).needs_review
