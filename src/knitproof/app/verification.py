"""Vérifier un fichier de patron : lecture, validation, constats du moteur."""

from pathlib import Path

from knitproof.app.errors import InputFileError, load_model
from knitproof.domain.pattern import Pattern
from knitproof.domain.report import Report
from knitproof.engine.report import build_report, from_finding
from knitproof.engine.verification import verify

PatternFileError = InputFileError


def verify_pattern(path: Path) -> Report:
    """Rapport du moteur sur le patron YAML de `path`."""
    pattern = load_model(path, Pattern, "patron invalide")
    return build_report(from_finding(finding) for finding in verify(pattern))
