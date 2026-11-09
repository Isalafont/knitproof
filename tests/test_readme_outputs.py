"""Les blocs de sortie du README sont ceux des fichiers de référence (CLA-69)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TAG = re.compile(
    r"<!-- sortie : (?P<file>examples/sorties/\S+) -->\n```text\n(?P<block>.*?)\n```", re.DOTALL
)


def mismatches(readme: str, root: Path = ROOT) -> list[str]:
    """Les fichiers de référence dont le bloc du README diffère."""
    return [
        found["file"]
        for found in TAG.finditer(readme)
        if (root / found["file"]).read_text(encoding="utf-8").removesuffix("\n") != found["block"]
    ]


def test_the_readme_has_at_least_two_tagged_outputs() -> None:
    assert len(TAG.findall(README.read_text(encoding="utf-8"))) >= 2


def test_every_tagged_block_equals_its_reference_file() -> None:
    assert mismatches(README.read_text(encoding="utf-8")) == []


def test_a_changed_line_is_detected(tmp_path: Path) -> None:
    text = README.read_text(encoding="utf-8")
    changed = tmp_path / "README.md"
    changed.write_text(text.replace("88 m, multiple de 4", "89 m, multiple de 4"), encoding="utf-8")

    assert mismatches(changed.read_text(encoding="utf-8")) == [
        "examples/sorties/bonnet-3-ans.calc.txt"
    ]
