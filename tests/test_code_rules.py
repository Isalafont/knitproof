"""Les règles de code vérifiées par ruff et mypy mordent (CLA-61)."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BIN = Path(sys.executable).parent
RUFF = BIN / "ruff"
RUFF_LINE = re.compile(r"^(?P<path>[^:]+):\d+:\d+: (?P<code>[A-Z]+[0-9]+) ", re.MULTILINE)

MAGIC_IN_SRC = "src/knitproof/engine/sample.py"
TYPOGRAPHY_IN_SRC = "src/knitproof/domain/sample.py"
TEST_SAMPLE = "tests/test_sample.py"

RUFF_SOURCES = {
    MAGIC_IN_SRC: "def is_long(rounds: int) -> bool:\n    return rounds > 42\n",
    TYPOGRAPHY_IN_SRC: (
        '"""L\u2019heure\u202f; le tour\u00a0: « fini »."""\n\n'
        'LABEL = "l\u2019aiguille\u202f!"  # note\u00a0: permis\n'
    ),
    TEST_SAMPLE: (
        "import pytest\n\n\n"
        "def test_sample() -> None:\n"
        "    assert 1 + 1 != 42\n"
        "    with pytest.raises(ValueError):\n"
        '        int("a")\n'
    ),
}


def copy_config(project: Path) -> Path:
    pyproject = project / "pyproject.toml"
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", pyproject)
    return pyproject


def write(project: Path, relative: str, source: str) -> Path:
    path = project / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def run(command: list[str], cwd: Path) -> str:
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, timeout=120, check=False
    )
    return result.stdout


@pytest.fixture(scope="module")
def ruff_codes(tmp_path_factory: pytest.TempPathFactory) -> dict[str, set[str]]:
    project = tmp_path_factory.mktemp("ruff")
    copy_config(project)
    for relative, source in RUFF_SOURCES.items():
        write(project, relative, source)
    stdout = run(
        [str(RUFF), "check", "--no-cache", "--output-format", "concise", "src", "tests"],
        project,
    )
    codes: dict[str, set[str]] = {relative: set() for relative in RUFF_SOURCES}
    for match in RUFF_LINE.finditer(stdout):
        codes.setdefault(match["path"], set()).add(match["code"])
    return codes


def test_magic_number_in_src_is_reported(ruff_codes: dict[str, set[str]]) -> None:
    assert "PLR2004" in ruff_codes[MAGIC_IN_SRC]


def test_magic_number_in_tests_is_allowed(ruff_codes: dict[str, set[str]]) -> None:
    assert "PLR2004" not in ruff_codes[TEST_SAMPLE]


def test_broad_pytest_raises_is_reported(ruff_codes: dict[str, set[str]]) -> None:
    assert "PT011" in ruff_codes[TEST_SAMPLE]


def test_french_typography_is_allowed(ruff_codes: dict[str, set[str]]) -> None:
    assert not {"RUF001", "RUF002", "RUF003"} & ruff_codes[TYPOGRAPHY_IN_SRC]
