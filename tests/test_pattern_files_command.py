"""La commande documentée « Vérifier un patron YAML » du README (CLA-75)."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VARIABLE = "KNITPROOF_PATTERNS"


def _run(patterns: str | None) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key != VARIABLE}
    if patterns is not None:
        env[VARIABLE] = patterns
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-rs",
            "tests/test_pattern_files.py",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_without_the_variable_the_check_is_skipped_with_its_reason() -> None:
    result = _run(None)

    assert result.returncode == 0
    assert f"{VARIABLE} absente" in result.stdout


def test_right_synthetic_patterns_pass() -> None:
    result = _run("examples/synthetiques/**/*.yaml")

    assert result.returncode == 0
    assert "1 passed" in result.stdout


def test_wrong_pattern_fails_with_round_computed_and_stated_counts() -> None:
    result = _run("examples/bonnet-erreur-rang-33.yaml")

    assert result.returncode == 1
    assert "Rang 33" in result.stdout
    assert "Annoncé : 89 m · Calculé : 90 m" in result.stdout


def test_pattern_matching_no_file_fails() -> None:
    result = _run("examples/absent-*.yaml")

    assert result.returncode == 1
    assert "aucun fichier trouvé" in result.stdout


def test_invalid_pattern_fails_with_the_validation_error() -> None:
    result = _run("examples/bonnet-3-ans.yaml")

    assert result.returncode == 1
    assert "fichier illisible ou invalide" in result.stdout
