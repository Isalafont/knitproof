"""Entrées du rapport depuis constats, avis, contrôles de montage et d’aiguilles (CLA-69)."""

from decimal import Decimal

from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.location import SourceLocation
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.needle import Needle, NeedleKind, NeedleMaterial, NeedleSize, NeedleSystem
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.question import PendingQuestion
from knitproof.domain.report import DecidedBy, ReportStatus
from knitproof.engine.cast_on import check_cast_on
from knitproof.engine.needle import check_needles
from knitproof.engine.report import (
    build_report,
    from_cast_on_check,
    from_finding,
    from_needle_check,
    from_notice,
)

SWATCH = SwatchMeasurement(
    stitches=Decimal(20), width=Length(value=Decimal(10), unit=LengthUnit.CM)
)


def _needle(size: str, system: NeedleSystem = NeedleSystem.MM, **extra: object) -> Needle:
    return Needle.model_validate(
        {"size": NeedleSize(system=system, original=size), "kind": NeedleKind.STRAIGHT, **extra}
    )


def test_a_finding_becomes_an_error_with_its_lines() -> None:
    finding = Finding(
        status=FindingStatus.ERROR,
        code=FindingCode.COUNT_MISMATCH,
        round=33,
        expected=90,
        actual=89,
        location=SourceLocation(page=2, line=14),
    )

    entry = from_finding(finding)

    assert entry.status is ReportStatus.ERROR
    assert entry.code == "count_mismatch"
    assert entry.round == 33
    assert entry.lines == (
        "nombre de mailles incohérent",
        "Annoncé : 89 m · Calculé : 90 m",
        "Source : page 2, ligne 14",
    )
    assert entry.decided_by is DecidedBy.ENGINE


def test_a_repeat_finding_without_location_has_no_source_line() -> None:
    finding = Finding(
        status=FindingStatus.ERROR,
        code=FindingCode.REPEAT_NOT_FITTING,
        round=31,
        expected=99,
        actual=100,
    )

    assert from_finding(finding).lines == (
        "les opérations ne tombent pas juste",
        "Rang précédent : 99 m · Consommées par les opérations : 100 m",
    )


def test_a_notice_keeps_status_code_round_and_text() -> None:
    notice = Notice(
        status=NoticeStatus.NEEDS_REVIEW,
        code=NoticeCode.CROWN_TOO_SMALL,
        text="calotte trop petite",
        round=12,
    )

    entry = from_notice(notice)

    assert entry.status is ReportStatus.NEEDS_REVIEW
    assert entry.code == "crown_too_small"
    assert entry.round == 12
    assert entry.lines == ("calotte trop petite",)


def test_a_warning_notice_stays_a_warning() -> None:
    notice = Notice(status=NoticeStatus.WARNING, code=NoticeCode.NEEDLE_CHANGE, text="t")

    assert from_notice(notice).status is ReportStatus.WARNING


def test_a_rejected_cast_on_gives_the_finished_width() -> None:
    check = check_cast_on(120, Length(value=Decimal("43.2"), unit=LengthUnit.CM), SWATCH, _mult())

    entry = from_cast_on_check(check, SWATCH)

    assert entry is not None
    assert entry.status is ReportStatus.REJECTED
    assert entry.code == "differs_from_calculation"
    assert entry.round is None
    assert "Après blocage, 120 m donnent 60 cm (120 \N{MULTIPLICATION SIGN} 10 / 20)" in entry.lines


def test_a_decimal_width_uses_the_decimal_comma() -> None:
    check = check_cast_on(121, Length(value=Decimal("43.2"), unit=LengthUnit.CM), SWATCH, _mult())

    entry = from_cast_on_check(check, SWATCH)

    assert entry is not None
    assert (
        "Après blocage, 121 m donnent 60,5 cm (121 \N{MULTIPLICATION SIGN} 10 / 20)" in entry.lines
    )


def test_an_accepted_cast_on_gives_no_entry() -> None:
    check = check_cast_on(88, Length(value=Decimal("43.2"), unit=LengthUnit.CM), SWATCH, _mult())

    assert from_cast_on_check(check, SWATCH) is None


def test_matching_needles_give_no_entry() -> None:
    assert from_needle_check(check_needles(_needle("4"), _needle("4"))) is None


def test_needle_reasons_give_one_line_each() -> None:
    swatch = _needle("4", material=NeedleMaterial.WOOD)
    project = _needle("5", material=NeedleMaterial.METAL)

    entry = from_needle_check(check_needles(swatch, project))

    assert entry is not None
    assert entry.status is ReportStatus.WARNING
    assert entry.code == "swatch_needle_mismatch"
    assert entry.lines == (
        "taille différente : la jauge de l’échantillon peut ne plus valoir pour le projet",
        "matière différente : la tension peut changer selon la personne",
    )


def test_sizes_in_two_systems_are_not_compared() -> None:
    entry = from_needle_check(check_needles(_needle("4"), _needle("6", NeedleSystem.US)))

    assert entry is not None
    assert entry.lines == ("À VÉRIFIER : tailles écrites dans deux systèmes, non comparées",)


def test_build_report_keeps_the_order_of_entry_without_sorting() -> None:
    warning = from_notice(
        Notice(status=NoticeStatus.WARNING, code=NoticeCode.NEEDLE_CHANGE, text="a")
    )
    error = from_finding(
        Finding(
            status=FindingStatus.ERROR,
            code=FindingCode.COUNT_MISMATCH,
            round=1,
            expected=2,
            actual=3,
        )
    )
    question = PendingQuestion(code="q", text="Quelle jauge ?", options=())

    report = build_report([warning, error], questions=[question])

    assert report.entries == (warning, error)
    assert report.questions == (question,)
    assert report.has_errors


def _mult() -> StitchMultiple:
    return StitchMultiple(repeat_multiple=4, repeat_offset=0)
