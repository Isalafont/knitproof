"""Erreurs de saisie lisibles : une ligne par champ, en français (CLA-69, CLA-108, CLA-76)."""

from pathlib import Path

import pytest

from knitproof.app.errors import InputFileError
from knitproof.app.verification import PatternFileError
from knitproof.cli.main import main

RAW_NOISE = ("Value error, ", "Unable to extract tag", "Tuple should have", "Input should be")


def _run(tmp_path: Path, text: str, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    path = tmp_path / "patron.yaml"
    path.write_text(text, encoding="utf-8")
    code = main(["verify", str(path)])
    captured = capsys.readouterr()
    assert captured.out == ""
    return code, captured.err


def test_pattern_file_error_is_the_input_file_error() -> None:
    assert PatternFileError is InputFileError


def test_zero_and_empty_rounds_give_one_french_line_per_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, err = _run(tmp_path, "cast_on: 0\nrounds: []\n", capsys)

    assert code == 3
    assert err.splitlines()[1:] == [
        "cast_on : doit être supérieur à 0",
        "rounds : au moins un rang",
    ]


def test_a_missing_field_and_an_unknown_key_are_named(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, err = _run(tmp_path, "rounds:\n  - start: 1\n    ops: [{work: 10}]\nautre: 1\n", capsys)

    assert code == 3
    assert "cast_on : champ obligatoire" in err
    assert "autre : clé inconnue" in err


def test_a_boolean_count_asks_for_an_integer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, err = _run(
        tmp_path, "cast_on: true\nrounds:\n  - start: 1\n    ops: [{work: 1}]\n", capsys
    )

    assert code == 3
    assert "cast_on : un entier est attendu" in err


@pytest.mark.parametrize(
    "text",
    [
        "cast_on: 0\nrounds: []\n",
        "cast_on: 10\nrounds:\n  - start: 1\n    ops: [{purl: 10}]\n",
        "cast_on: 10\nrounds:\n  - start: 2\n    ops: [{work: 10}]\n",
        "cast_on: x\nrounds:\n  - start: 1\n    ops: [{work: -1}]\n",
    ],
)
def test_no_message_keeps_the_raw_pydantic_noise(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str
) -> None:
    code, err = _run(tmp_path, text, capsys)

    assert code == 3
    assert not any(noise in err for noise in RAW_NOISE)
