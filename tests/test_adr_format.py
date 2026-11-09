"""Les ADR suivent le format court de `docs/adr/README.md` (CLA-124)."""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = PROJECT_ROOT / "docs" / "adr"
MAX_LINES = 40
# Raccourcis par CLA-122, qui vide cette liste.
EXEMPT = frozenset({"0018", "0019", "0020", "0021", "0023", "0024", "0026"})
SUITES = re.compile(r"^## Suites", re.MULTILINE)
LINE_NUMBER = re.compile(r"\b[lL]\. ?\d+")


def test_adrs_follow_the_short_format() -> None:
    problems = [
        problem
        for path in _adr_paths()
        if path.name[:4] not in EXEMPT
        for problem in adr_problems(path.name, path.read_text(encoding="utf-8"))
    ]
    if problems:
        pytest.fail("\n".join(problems), pytrace=False)


def test_exemptions_name_existing_adrs() -> None:
    numbers = {path.name[:4] for path in _adr_paths()}
    assert numbers >= EXEMPT


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("# ADR 0099\n" + "ligne\n" * 40, "41 lignes"),
        ("# ADR 0099\n\n## Suites\n\n- CLA-1\n", "section « Suites »"),
        ("# ADR 0099\n\n- `docs/architecture.md` (l. 182)\n", "numéro de ligne"),
        ("# ADR 0099\n\nL.255 : règle\n", "numéro de ligne"),
    ],
)
def test_a_non_compliant_adr_is_named(text: str, reason: str) -> None:
    problems = adr_problems("0099-exemple.md", text)
    assert problems
    assert all(problem.startswith("0099-exemple.md") for problem in problems)
    assert any(reason in problem for problem in problems)


def test_an_adr_of_exactly_the_limit_passes() -> None:
    assert adr_problems("0099-exemple.md", "# ADR 0099\n" + "ligne\n" * 39) == []


def test_business_text_is_not_a_line_number() -> None:
    text = "# ADR 0099\n\nLa ligne 18,0 ans et la ligne 14号 restent.\n"
    assert adr_problems("0099-exemple.md", text) == []


def adr_problems(name: str, text: str) -> list[str]:
    problems: list[str] = []
    count = len(text.splitlines())
    if count > MAX_LINES:
        problems.append(f"{name} : {count} lignes, {MAX_LINES} au plus")
    if SUITES.search(text):
        problems.append(f"{name} : section « Suites »")
    match = LINE_NUMBER.search(text)
    if match:
        problems.append(f"{name} : numéro de ligne « {match.group()} »")
    return problems


def _adr_paths() -> list[Path]:
    return sorted(ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))
