"""Vérification à la demande des patrons désignés par `KNITPROOF_PATTERNS` (CLA-75).

Sans la variable, le test est sauté : la CI ne lit aucun patron privé.
"""

import glob
import os
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from knitproof.domain.finding import Finding, FindingCode
from knitproof.domain.pattern import Pattern
from knitproof.engine.verification import verify

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
        pattern = Pattern.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, yaml.YAMLError, ValidationError) as error:
        return [f"{path} : fichier illisible ou invalide\n{error}"]
    return [f"{path} : {_describe(finding)}" for finding in verify(pattern)]


def _describe(finding: Finding) -> str:
    if finding.code is FindingCode.COUNT_MISMATCH:
        return (
            f"tour {finding.round} — count_mismatch : "
            f"calculé {finding.expected} m, annoncé {finding.actual} m"
        )
    return (
        f"tour {finding.round} — repeat_not_fitting : le tour précédent laisse "
        f"{finding.expected} m, les opérations en consomment {finding.actual}"
    )
