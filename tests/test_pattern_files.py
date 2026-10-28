"""Vérification à la demande des patrons désignés par `KNITPROOF_PATTERNS` (CLA-75).

Sans la variable, le test est sauté : la CI ne lit aucun patron privé.
"""

import glob
import os
from pathlib import Path

import pytest

from knitproof.app.verification import PatternFileError, verify_pattern
from knitproof.cli.report import render

VARIABLE = "KNITPROOF_PATTERNS"


def test_requested_pattern_files_have_no_finding() -> None:
    requested = os.environ.get(VARIABLE, "").strip()
    if not requested:
        pytest.skip(f"{VARIABLE} absente : aucun patron à vérifier")
    paths = sorted(Path(match) for match in glob.glob(requested, recursive=True))
    if not paths:
        pytest.fail(f"{VARIABLE}={requested} : aucun fichier trouvé", pytrace=False)
    problems = [problem for path in paths for problem in _problems(path)]
    if problems:
        pytest.fail("\n".join(problems), pytrace=False)


def _problems(path: Path) -> list[str]:
    try:
        findings = verify_pattern(path)
    except PatternFileError as error:
        return [f"{path} : fichier illisible ou invalide\n{error.reason}"]
    return [f"{path}\n{render(findings)}"] if findings else []
