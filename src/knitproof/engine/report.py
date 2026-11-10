"""Entrées du rapport : les textes viennent d’ici, `cli` ne fait que les mettre en colonnes."""

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal
from typing import assert_never

from knitproof.domain.beanie import BeaniePlan
from knitproof.domain.cast_on import CastOnCheck, CastOnRejection
from knitproof.domain.finding import Finding, FindingCode
from knitproof.domain.gauge import GaugeSource
from knitproof.domain.measure import SwatchMeasurement
from knitproof.domain.needle import NeedleCheck, NeedleMismatch
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.question import PendingQuestion
from knitproof.domain.report import DecidedBy, Report, ReportEntry, ReportStatus

_GAUGE_LEAD = {
    GaugeSource.BLOCKED: "Après blocage",
    GaugeSource.UNBLOCKED: "Avec l’échantillon avant blocage",
    GaugeSource.LABEL: "Avec la jauge de l’étiquette",
}
NEEDLE_MISMATCH_CODE = "swatch_needle_mismatch"
TIMES = "\N{MULTIPLICATION SIGN}"  # RUF001 refuse le caractère écrit en clair


def build_report(
    entries: Iterable[ReportEntry],
    questions: Iterable[PendingQuestion] = (),
    result: BeaniePlan | None = None,
) -> Report:
    """Rapport dans l’ordre d’entrée, sans tri par statut."""
    return Report(entries=tuple(entries), questions=tuple(questions), result=result)


def from_finding(finding: Finding) -> ReportEntry:
    """Titre, détail du compte, puis source si le fichier la donne."""
    match finding.code:
        case FindingCode.COUNT_MISMATCH:
            title = "nombre de mailles incohérent"
            detail = f"Annoncé : {finding.actual} m · Calculé : {finding.expected} m"
        case FindingCode.REPEAT_NOT_FITTING:
            title = "les opérations ne tombent pas juste"
            detail = (
                f"Rang précédent : {finding.expected} m · "
                f"Consommées par les opérations : {finding.actual} m"
            )
        case _:
            assert_never(finding.code)
    lines = [title, detail]
    if finding.location is not None:
        lines.append(_source(finding.location.page, finding.location.line))
    return ReportEntry(
        status=ReportStatus.ERROR,
        code=finding.code.value,
        round=finding.round,
        lines=tuple(lines),
        decided_by=DecidedBy.ENGINE,
    )


def from_notice(notice: Notice) -> ReportEntry:
    status = {
        NoticeStatus.WARNING: ReportStatus.WARNING,
        NoticeStatus.NEEDS_REVIEW: ReportStatus.NEEDS_REVIEW,
    }[notice.status]
    return ReportEntry(
        status=status,
        code=notice.code.value,
        round=notice.round,
        lines=tuple(notice.text.splitlines()),
        decided_by=DecidedBy.ENGINE,
    )


def unblocked_swatch_notice(
    check: CastOnCheck, before_blocking: SwatchMeasurement
) -> Notice | None:
    """Alerte : le montage sur l’échantillon avant blocage, et la largeur qu’il donnerait.

    `check` contrôle ce montage contre le calcul après blocage ; `None` s’ils concordent.
    """
    if check.expected == check.proposed:
        return None
    text = (
        f"Avec l’échantillon avant blocage ({_number(before_blocking.stitches)} m), "
        f"on monterait {check.proposed} m.\n"
        f"{check.proposed} m donneraient {_number(check.proposed_finished_cm)} cm après blocage, "
        "sans aisance."
    )
    return Notice(status=NoticeStatus.WARNING, code=NoticeCode.UNBLOCKED_SWATCH_CAST_ON, text=text)


def from_cast_on_check(
    check: CastOnCheck,
    swatch: SwatchMeasurement,
    title: str | None = None,
    source: GaugeSource = GaugeSource.BLOCKED,
) -> ReportEntry | None:
    """Un montage proposé rejeté, avec la largeur finie qu’il donnerait ; `None` si accepté.

    `source` nomme d’où vient la jauge : « Après blocage » seulement pour un échantillon bloqué.
    """
    if check.accepted:
        return None
    width = _number(swatch.width.in_cm)
    lines = [
        *([title] if title is not None else []),
        *(_rejection_text(reason, check) for reason in check.reasons),
        f"{_GAUGE_LEAD[source]}, {check.proposed} m donnent "
        f"{_number(check.proposed_finished_cm)} cm "
        f"({check.proposed} {TIMES} {width} / {_number(swatch.stitches)})",
    ]
    return ReportEntry(
        status=ReportStatus.REJECTED,
        code=check.reasons[0].value,
        round=None,
        lines=tuple(lines),
        decided_by=DecidedBy.ENGINE,
    )


def from_needle_check(check: NeedleCheck) -> ReportEntry | None:
    """Une ligne par raison ; `None` si les aiguilles concordent."""
    if check.matches:
        return None
    return ReportEntry(
        status=ReportStatus.WARNING,
        code=NEEDLE_MISMATCH_CODE,
        round=None,
        lines=tuple(_mismatch_text(reason) for reason in check.reasons),
        decided_by=DecidedBy.ENGINE,
    )


def _rejection_text(reason: CastOnRejection, check: CastOnCheck) -> str:
    match reason:
        case CastOnRejection.STITCH_MULTIPLE_NOT_RESPECTED:
            return f"{check.proposed} m ne respectent pas le multiple du point"
        case CastOnRejection.DIFFERS_FROM_CALCULATION:
            return f"{check.proposed} m diffèrent du montage calculé : {check.expected} m"
        case _:
            assert_never(reason)


def _mismatch_text(reason: NeedleMismatch) -> str:
    match reason:
        case NeedleMismatch.SIZE_DIFFERS:
            return (
                "taille différente : la jauge de l’échantillon peut ne plus valoir pour le projet"
            )
        case NeedleMismatch.SIZES_NOT_COMPARABLE:
            return "À VÉRIFIER : tailles écrites dans deux systèmes, non comparées"
        case NeedleMismatch.MATERIAL_DIFFERS:
            return "matière différente : la tension peut changer selon la personne"
        case _:
            assert_never(reason)


def _source(page: int | None, line: int | None) -> str:
    parts = []
    if page is not None:
        parts.append(f"page {page}")
    if line is not None:
        parts.append(f"ligne {line}")
    return "Source : " + ", ".join(parts)


def _number(value: Decimal) -> str:
    """Nombre en texte à la virgule, sans zéros inutiles ; au plus deux décimales, à l’affichage."""
    shown = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    text = format(shown.normalize(), "f") if shown != value else format(value.normalize(), "f")
    return text.replace(".", ",")
