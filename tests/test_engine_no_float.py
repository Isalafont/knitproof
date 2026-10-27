"""Aucun `float` dans `engine` : les comptes de mailles sont des entiers (ADR 0007)."""

import ast
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "src" / "knitproof" / "engine"


def floats(source: str) -> list[str]:
    """Nomme chaque `float`, constante flottante ou division `/` du source."""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name) and node.id == "float":
            found.append(f"ligne {node.lineno} : nom float")
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            found.append(f"ligne {node.lineno} : constante {node.value}")
        elif isinstance(node, ast.BinOp | ast.AugAssign) and isinstance(node.op, ast.Div):
            found.append(f"ligne {node.lineno} : division /")
    return found


def test_engine_sources_have_no_float() -> None:
    sources = sorted(ENGINE.rglob("*.py"))

    assert sources
    for source in sources:
        assert floats(source.read_text(encoding="utf-8")) == [], source.name


@pytest.mark.parametrize(
    "source",
    ["x = 1.5", "x: float = 1", "y = n / 2", "n /= 2", "return round(n / 2)"],
)
def test_the_check_bites(source: str) -> None:
    if source.startswith("return"):
        source = f"def half(n: int) -> int:\n    {source}"

    assert floats(source) != []


def test_the_check_lets_integer_code_through() -> None:
    assert floats("y = n // 2\nz = Decimal('1.5')") == []
