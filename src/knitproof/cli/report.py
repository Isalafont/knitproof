"""Rapport en texte : met en colonnes les entrées du rapport, ne calcule rien."""

from typing import assert_never

from knitproof.domain.report import Report, ReportEntry, ReportStatus

_OK_LABEL = "OK"
_COLUMN = 12
_INDENT = " " * _COLUMN


def render(report: Report) -> str:
    """Un bloc par entrée, séparés par une ligne vide ; une ligne « OK » sans entrée."""
    if not report.entries:
        return f"{_OK_LABEL:<{_COLUMN}}Aucun écart sur les comptes vérifiés."
    return "\n\n".join(_describe(entry) for entry in report.entries)


def _describe(entry: ReportEntry) -> str:
    first, *rest = entry.lines
    title = first if entry.round is None else f"Rang {entry.round} — {first}"
    lines = [*rest, f"Décidé par : {entry.decided_by.label}"]
    head = f"{_status_label(entry.status):<{_COLUMN}}{title}"
    return "\n".join([head, *(f"{_INDENT}{line}" for line in lines)])


def _status_label(status: ReportStatus) -> str:
    match status:
        case ReportStatus.ERROR:
            return "ERREUR"
        case ReportStatus.WARNING:
            return "ALERTE"
        case ReportStatus.NEEDS_REVIEW:
            return "À VÉRIFIER"
        case ReportStatus.REJECTED:
            return "REJETÉ"
        case _:
            assert_never(status)
