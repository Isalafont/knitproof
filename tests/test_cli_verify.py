"""`knitproof verify` : rapport, codes de sortie 0, 1, 2 et 3 (CLA-76)."""

import subprocess
import sysconfig
from pathlib import Path

import pytest

from knitproof.cli.main import main

EXAMPLES = Path(__file__).parent.parent / "examples"
KNITPROOF = Path(sysconfig.get_path("scripts")) / "knitproof"


def test_findings_exit_1_with_the_report_on_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["verify", str(EXAMPLES / "bonnet-erreur-rang-33.yaml")])

    captured = capsys.readouterr()
    assert code == 1
    assert "Rang 33" in captured.out
    assert captured.err == ""


def test_no_finding_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    path = EXAMPLES / "synthetiques" / "bonnets" / "bonnet-synthetique.yaml"

    code = main(["verify", str(path)])

    assert code == 0
    assert "Aucun écart sur les comptes vérifiés." in capsys.readouterr().out


def test_missing_file_exits_3_on_stderr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["verify", str(tmp_path / "absent.yaml")])

    captured = capsys.readouterr()
    assert code == 3
    assert captured.out == ""
    assert "introuvable" in captured.err


def test_pattern_starting_at_round_2_exits_3_in_rangs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "patron.yaml"
    path.write_text("cast_on: 10\nrounds:\n  - start: 2\n    ops:\n      - work: 10\n")

    code = main(["verify", str(path)])

    assert code == 3
    assert "rang" in capsys.readouterr().err


def test_unknown_operation_exits_3_in_rangs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "patron.yaml"
    path.write_text("cast_on: 10\nrounds:\n  - start: 1\n    ops:\n      - purl: 10\n")

    code = main(["verify", str(path)])

    captured = capsys.readouterr()
    assert code == 3
    assert "rang" in captured.err


def test_deeply_nested_file_exits_3(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "patron.yaml"
    path.write_bytes(b"[" * 5000 + b"]" * 5000 + b"\n")

    code = main(["verify", str(path)])

    captured = capsys.readouterr()
    assert code == 3
    assert "imbrication trop profonde" in captured.err


def test_usage_error_exits_2() -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["verify"])

    assert exit_.value.code == 2


@pytest.mark.parametrize("content", [b"cast_on: [\n", b"\xff\xfe", b"rounds: []\n"])
def test_invalid_file_exits_3_without_traceback(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "patron.yaml"
    path.write_bytes(content)

    result = subprocess.run(
        [str(KNITPROOF), "verify", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 3
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
