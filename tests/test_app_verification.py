"""`verify_pattern` : lecture, validation et constats, erreurs de fichier enveloppées (CLA-76)."""

from pathlib import Path

import pytest

from knitproof.app.verification import PatternFileError, verify_pattern
from knitproof.domain.finding import FindingCode
from knitproof.domain.location import SourceLocation

EXAMPLES = Path(__file__).parent.parent / "examples"
DEEP_YAML = b"[" * 5000 + b"]" * 5000 + b"\n"


def _unknown_op_at(start: str | None, end: str | None = None, before: int = 0) -> bytes:
    """Patron dont un rang a une opération inconnue, après `before` rangs valides."""
    lines = ["cast_on: 10", "rounds:"]
    if before:
        lines.append(f"  - {{start: 1, end: {before}, ops: [{{work: 10}}]}}")
    lines.append("  - ops: [{purl: 10}]")
    if start is not None:
        lines.append(f"    start: {start}")
    if end is not None:
        lines.append(f"    end: {end}")
    return ("\n".join(lines) + "\n").encode()


def test_count_mismatch_is_reported_at_round_33() -> None:
    findings = verify_pattern(EXAMPLES / "bonnet-erreur-rang-33.yaml")

    assert [(f.code, f.round, f.expected, f.actual) for f in findings] == [
        (FindingCode.COUNT_MISMATCH, 33, 90, 89)
    ]
    assert findings[0].location == SourceLocation(page=2, line=14)


def test_right_pattern_gives_no_finding() -> None:
    path = EXAMPLES / "synthetiques" / "bonnets" / "bonnet-synthetique.yaml"

    assert verify_pattern(path) == []


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        (None, "introuvable"),
        (b"\xff\xfe", "pas en UTF-8"),
        (b"cast_on: [\n", "YAML mal formé"),
        (b"", "patron invalide"),
        (b"cast_on: 10\nrounds:\n  - start: 2\n    ops:\n      - work: 10\n", "rang 2"),
        (DEEP_YAML, "imbrication trop profonde"),
        (_unknown_op_at(start="33"), "rang 33, ops"),
        (_unknown_op_at(start="10", end="20", before=9), "rangs 10 à 20, ops"),
        (_unknown_op_at(start=None), r"rounds\.0\.ops\.0"),
        (_unknown_op_at(start="abc"), r"rounds\.0\.ops\.0"),
    ],
)
def test_unreadable_or_invalid_file_raises_pattern_file_error(
    tmp_path: Path, content: bytes | None, reason: str
) -> None:
    path = tmp_path / "patron.yaml"
    if content is not None:
        path.write_bytes(content)

    with pytest.raises(PatternFileError, match=reason) as raised:
        verify_pattern(path)

    assert raised.value.path == path


def test_directory_raises_pattern_file_error(tmp_path: Path) -> None:
    with pytest.raises(PatternFileError, match="lecture impossible"):
        verify_pattern(tmp_path)


def test_validation_errors_are_condensed_to_one_line_each(tmp_path: Path) -> None:
    path = tmp_path / "patron.yaml"
    path.write_bytes(b"")

    with pytest.raises(PatternFileError) as raised:
        verify_pattern(path)

    lines = raised.value.reason.splitlines()
    assert lines[0] == "patron invalide"
    assert all(line and not line.startswith(" ") for line in lines[1:])


def test_error_on_start_keeps_the_raw_location_and_shows_no_round_zero(tmp_path: Path) -> None:
    path = tmp_path / "patron.yaml"
    path.write_bytes(b"cast_on: 10\nrounds:\n  - start: 0\n    ops: [{work: 10}]\n")

    with pytest.raises(PatternFileError) as raised:
        verify_pattern(path)

    assert "rounds.0.start" in raised.value.reason
    assert "rang 0" not in raised.value.reason
