import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LINT_IMPORTS = Path(sys.executable).with_name("lint-imports")

Mutation = Callable[[Path], None]


def lint_imports(project: Path, pythonpath: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if pythonpath is not None:
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(pythonpath), env.get("PYTHONPATH")]))
    return subprocess.run(
        [str(LINT_IMPORTS), "--config", str(project / "pyproject.toml"), "--no-cache", "--no-logo"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def add_import(source: str, target: str) -> Mutation:
    def mutate(src: Path) -> None:
        init = src / "knitproof" / source / "__init__.py"
        init.write_text(init.read_text() + f"from knitproof import {target}\n")

    return mutate


def add_package(name: str) -> Mutation:
    def mutate(src: Path) -> None:
        package = src / "knitproof" / name
        package.mkdir()
        (package / "__init__.py").touch()

    return mutate


@pytest.fixture
def project_copy(tmp_path: Path) -> Path:
    shutil.copytree(
        PROJECT_ROOT / "src", tmp_path / "src", ignore=shutil.ignore_patterns("__pycache__")
    )
    shutil.copy2(PROJECT_ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    return tmp_path


def test_project_respects_layer_contracts() -> None:
    result = lint_imports(PROJECT_ROOT)
    assert result.returncode == 0, result.stdout


def test_unmodified_copy_respects_layer_contracts(project_copy: Path) -> None:
    result = lint_imports(project_copy, pythonpath=project_copy / "src")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(
            add_import("engine", "llm"), "knitproof.engine -> knitproof.llm", id="engine-llm"
        ),
        pytest.param(
            add_import("engine", "library"),
            "knitproof.engine -> knitproof.library",
            id="engine-library",
        ),
        pytest.param(
            add_import("domain", "engine"),
            "knitproof.domain -> knitproof.engine",
            id="domain-engine",
        ),
        pytest.param(
            add_import("cli", "engine"), "knitproof.cli -> knitproof.engine", id="cli-engine"
        ),
        pytest.param(
            add_import("evals", "engine"),
            "knitproof.evals -> knitproof.engine",
            id="evals-engine",
        ),
        pytest.param(add_package("rogue"), "knitproof.rogue", id="undeclared-package"),
    ],
)
def test_violation_breaks_layer_contracts(
    project_copy: Path, mutate: Mutation, expected: str
) -> None:
    mutate(project_copy / "src")
    result = lint_imports(project_copy, pythonpath=project_copy / "src")
    assert result.returncode == 1
    assert expected in result.stdout
