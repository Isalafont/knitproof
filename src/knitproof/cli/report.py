"""Rapport de vérification en texte : met en forme les constats, ne calcule rien."""

from collections.abc import Sequence
from typing import assert_never

from knitproof.domain.finding import Finding, FindingCode, FindingStatus

_STATUS_LABELS = {FindingStatus.ERROR: "ERREUR"}
_OK_LABEL = "OK"
_COLUMN = max(len(label) for label in (*_STATUS_LABELS.values(), _OK_LABEL)) + 6
_INDENT = " " * _COLUMN


def render(findings: Sequence[Finding]) -> str:
    """Un bloc par constat, séparés par une ligne vide ; une ligne « OK » sans constat."""
    if not findings:
        return f"{_OK_LABEL:<{_COLUMN}}Aucun écart sur les comptes vérifiés."
    return "\n\n".join(_describe(finding) for finding in findings)


def _describe(finding: Finding) -> str:
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
    lines = [f"{_status_label(finding.status):<{_COLUMN}}Rang {finding.round} — {title}", detail]
    if finding.location is not None:
        lines.append(_source(finding.location.page, finding.location.line))
    lines.append("Décidé par : le moteur (calcul vérifiable)")
    return "\n".join([lines[0], *(f"{_INDENT}{line}" for line in lines[1:])])


def _status_label(status: FindingStatus) -> str:
    match status:
        case FindingStatus.ERROR:
            return _STATUS_LABELS[status]
        case _:
            assert_never(status)


def _source(page: int | None, line: int | None) -> str:
    parts = []
    if page is not None:
        parts.append(f"page {page}")
    if line is not None:
        parts.append(f"ligne {line}")
    return "Source : " + ", ".join(parts)
