"""`render` : rapport de vérification en rangs, sans calcul (CLA-76)."""

import datetime
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from knitproof.app.baseline import BaselineResult, ProviderResult
from knitproof.app.eval_cases import Split
from knitproof.cli.report import render as render_report
from knitproof.cli.report import render_baseline
from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.location import SourceLocation
from knitproof.domain.report import Report
from knitproof.engine.report import build_report, from_finding


def render(findings: Sequence[Finding]) -> str:
    report: Report = build_report(from_finding(finding) for finding in findings)
    return render_report(report)


def _finding(
    code: FindingCode,
    round_: int,
    expected: int,
    actual: int,
    location: SourceLocation | None = None,
) -> Finding:
    return Finding(
        status=FindingStatus.ERROR,
        code=code,
        round=round_,
        expected=expected,
        actual=actual,
        location=location,
    )


def test_no_finding_gives_a_single_ok_line() -> None:
    assert render([]) == "OK          Aucun écart sur les comptes vérifiés."


def test_count_mismatch_block() -> None:
    finding = _finding(FindingCode.COUNT_MISMATCH, 33, 90, 89, SourceLocation(page=2, line=14))

    assert render([finding]) == (
        "ERREUR      Rang 33 — nombre de mailles incohérent\n"
        "            Annoncé : 89 m · Calculé : 90 m\n"
        "            Source : page 2, ligne 14\n"
        "            Décidé par : le moteur (calcul vérifiable)"
    )


def test_repeat_not_fitting_block() -> None:
    finding = _finding(FindingCode.REPEAT_NOT_FITTING, 31, 99, 100)

    assert render([finding]) == (
        "ERREUR      Rang 31 — les opérations ne tombent pas juste\n"
        "            Rang précédent : 99 m · Consommées par les opérations : 100 m\n"
        "            Décidé par : le moteur (calcul vérifiable)"
    )


def test_source_shows_page_alone_or_line_alone() -> None:
    page = _finding(FindingCode.COUNT_MISMATCH, 2, 1, 2, SourceLocation(page=2))
    line = _finding(FindingCode.COUNT_MISMATCH, 2, 1, 2, SourceLocation(line=14))

    assert "            Source : page 2\n" in render([page])
    assert "            Source : ligne 14\n" in render([line])


def test_no_location_gives_no_source_line() -> None:
    finding = _finding(FindingCode.COUNT_MISMATCH, 2, 1, 2)

    assert "Source" not in render([finding])


def test_two_findings_are_separated_by_a_blank_line() -> None:
    first = _finding(FindingCode.COUNT_MISMATCH, 2, 1, 2)
    second = _finding(FindingCode.REPEAT_NOT_FITTING, 5, 3, 4)

    blocks = render([first, second]).split("\n\n")

    assert len(blocks) == 2
    assert blocks[0].startswith("ERREUR      Rang 2")
    assert blocks[1].startswith("ERREUR      Rang 5")


def _line(provider: str, model: str | None, host: str | None) -> ProviderResult:
    return ProviderResult(
        provider=provider,
        model=model,
        host=host,
        correct=18,
        wrong=0,
        abstentions=0,
        total=18,
        low=Decimal("0.8247"),
        high=Decimal("1"),
        runs=(),
    )


def test_a_baseline_line_is_named_by_provider_model_and_host() -> None:
    result = BaselineResult(
        split=Split.DEV,
        prompt_id="p",
        prompt_sha256="0" * 64,
        passes=3,
        measured_on=datetime.datetime(2026, 11, 17, 9, 30, tzinfo=datetime.UTC),
        providers=(
            _line("openrouter", "moonshotai/kimi-k3.1-pro", "moonshotai"),
            _line("anthropic", "claude-opus-5-5", None),
            _line("ollama", None, None),
        ),
    )

    lines = render_baseline(result, Path("r.yaml")).splitlines()

    assert lines[0].startswith("openrouter:moonshotai/kimi-k3.1-pro@moonshotai  18/18")
    assert lines[1].startswith("anthropic:claude-opus-5-5")
    assert lines[2].startswith("ollama ")
    assert len({line.index("18/18") for line in lines[:3]}) == 1
