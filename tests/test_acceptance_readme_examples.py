"""Tests d’acceptation des deux exemples du README, en attente de la CLI (tranche 6)."""

import re
import subprocess
import sysconfig
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT_ROOT / "examples"
KNITPROOF = Path(sysconfig.get_path("scripts")) / "knitproof"

PENDING_CLI = pytest.mark.xfail(
    raises=FileNotFoundError,
    strict=True,
    reason="la commande knitproof n’existe pas encore (tranche 6)",
)


def example(name: str) -> Path:
    path = EXAMPLES / name
    assert path.is_file(), f"exemple absent : {path}"
    return path


def knitproof(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(KNITPROOF), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def numbers(output: str) -> set[int]:
    return {int(n) for n in re.findall(r"\d+", output)}


@PENDING_CLI
def test_verify_reports_the_count_mismatch_at_round_33() -> None:
    pattern = example("bonnet-erreur-rang-33.yaml")

    result = knitproof("verify", str(pattern))

    assert result.returncode == 1
    assert {33, 90, 89} <= numbers(result.stdout)


@PENDING_CLI
def test_calc_casts_on_88_warns_at_96_and_rejects_120() -> None:
    request = example("bonnet-3-ans.yaml")

    result = knitproof("calc", str(request))

    assert {88, 96, 120} <= numbers(result.stdout)
