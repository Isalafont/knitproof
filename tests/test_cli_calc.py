"""`knitproof calc` : sortie de référence, codes de sortie 0, 1, 2 et 3 (CLA-69)."""

from pathlib import Path

import pytest
import yaml

from knitproof.cli.main import main

EXAMPLES = Path(__file__).parent.parent / "examples"
REQUEST = EXAMPLES / "bonnet-3-ans.yaml"
TIMES = "\N{MULTIPLICATION SIGN}"
MINUS = "\N{MINUS SIGN}"


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "demande.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_the_output_is_the_reference_file_byte_for_byte(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["calc", str(REQUEST)])

    expected = (EXAMPLES / "sorties" / "bonnet-3-ans.calc.txt").read_text("utf-8")
    assert code == 0
    assert capsys.readouterr().out == expected


def test_the_reference_file_shows_the_values_of_the_engine() -> None:
    expected = (EXAMPLES / "sorties" / "bonnet-3-ans.calc.txt").read_text("utf-8")

    for shown in ("86,4 m", "88 m", "44 cm", "75 rangs", "30 rangs", "28 rangs", "17 rangs"):
        assert shown in expected
    for shown in ("96 m", "48 cm", "120 m", "60 cm"):
        assert shown in expected


def test_without_row_gauge_exit_1_with_the_questions_on_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    data["swatch"]["after_blocking"] = {"stitches": "20", "width": {"value": "10", "unit": "cm"}}

    code = main(["calc", str(_write(tmp_path, yaml.safe_dump(data, allow_unicode=True)))])

    captured = capsys.readouterr()
    assert code == 1
    assert "Combien de rangs" in captured.out
    assert "Calotte" not in captured.out


def test_a_missing_file_exits_3_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["calc", str(tmp_path / "absent.yaml")])

    captured = capsys.readouterr()
    assert code == 3
    assert "introuvable" in captured.err
    assert captured.out == ""


def test_an_invalid_request_exits_3_without_raw_pydantic_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["calc", str(_write(tmp_path, "head_circumference: 48\nextra: 1\n"))])

    captured = capsys.readouterr()
    assert code == 3
    assert "demande de bonnet invalide" in captured.err
    assert "validation error" not in captured.err
    assert "pydantic" not in captured.err.lower()


def test_without_argument_exits_2() -> None:
    with pytest.raises(SystemExit) as raised:
        main(["calc"])

    assert raised.value.code == 2


def test_the_needle_text_is_rendered(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    data["needles"] = [{"size": "US 6", "kind": "double_pointed"}]

    main(["calc", str(_write(tmp_path, yaml.safe_dump(data, allow_unicode=True)))])

    out = capsys.readouterr().out
    assert "Aiguilles   US 6 : 4 ou 4,25 mm selon le CYC, À VÉRIFIER sur l’emballage" in out


def test_the_reference_file_shows_the_needles() -> None:
    expected = (EXAMPLES / "sorties" / "bonnet-3-ans.calc.txt").read_text("utf-8")

    assert "Aiguilles   4 mm\n" in expected


def test_the_row_gauge_source_is_shown_on_the_height_line() -> None:
    expected = (EXAMPLES / "sorties" / "bonnet-3-ans.calc.txt").read_text("utf-8")

    assert "(30 rangs / 10 cm, À VÉRIFIER, d’après DROPS Children 49-25)" in expected


def test_without_a_source_the_height_line_is_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    for key in ("before_blocking", "after_blocking"):
        del data["swatch"][key]["rows_source"]

    main(["calc", str(_write(tmp_path, yaml.safe_dump(data, allow_unicode=True)))])

    assert "75 rangs (30 rangs / 10 cm)\n" in capsys.readouterr().out


def _data() -> dict[str, object]:
    loaded = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _run(
    tmp_path: Path, data: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> tuple[int, str, str]:
    code = main(["calc", str(_write(tmp_path, yaml.safe_dump(data, allow_unicode=True)))])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _swatch(data: dict[str, object]) -> dict[str, object]:
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    return swatch


def test_a_before_blocking_swatch_alone_shows_its_source_to_verify(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    del _swatch(data)["after_blocking"]
    del data["proposed_cast_on"]

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 0
    assert "22 m / 10 cm, avant blocage, À VÉRIFIER (source : votre échantillon)" in out
    assert "bloquer (laver puis sécher)" in out
    assert "(30 rangs / 10 cm, À VÉRIFIER, d’après DROPS Children 49-25)" in out


def test_an_unknown_blocking_swatch_exits_1_with_the_question_and_no_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    swatch = _swatch(data)
    swatch["unknown_blocking"] = swatch.pop("after_blocking")
    del swatch["before_blocking"]

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 1
    assert "L’as-tu bloqué (lavé puis séché) ?" in out
    assert "Échantillon" not in out
    assert "Calotte" not in out


def test_unknown_blocking_with_another_measure_exits_3(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    swatch = _swatch(data)
    swatch["unknown_blocking"] = dict(swatch["after_blocking"])  # type: ignore[call-overload]

    code, _, err = _run(tmp_path, data, capsys)

    assert code == 3
    assert "unknown_blocking" in err


def test_a_label_without_swatch_shows_the_label_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    del data["swatch"], data["proposed_cast_on"]
    width = {"value": "10", "unit": "cm"}
    data["label_gauge"] = {"stitches": "20", "width": width, "rows": "30", "height": width}

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 0
    assert "20 m / 10 cm, étiquette, À VÉRIFIER (source : fabricant)" in out
    assert "jauge du fabricant, état de blocage inconnu" in out
    assert "(30 rangs / 10 cm)" in out


def test_neither_swatch_nor_label_exits_1_with_the_question(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    del data["swatch"], data["proposed_cast_on"]

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 1
    assert "QUESTION" in out
    assert "Échantillon" not in out


def test_a_swatch_far_from_the_label_warns_and_keeps_the_blocked_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    data["label_gauge"] = {"stitches": "24", "width": {"value": "10", "unit": "cm"}}

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 0
    assert "ALERTE" in out
    assert "pas assez de mailles pour 10 cm : aiguilles plus fines" in out
    assert "20 m / 10 cm, après blocage (source : votre échantillon)" in out


def test_a_head_in_inches_with_percent_ease_shows_the_formulas_in_cm(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    data["head_circumference"] = {"value": "20", "unit": "in", "provenance": "measured"}
    del data["proposed_cast_on"]

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 0
    assert f"Tour visé   45,72 cm (50,8 {TIMES} 0,9)" in out
    assert f"91,44 m calculées (45,72 {TIMES} 20 / 10) → 92 m" in out


def test_a_head_in_inches_with_cm_ease_shows_the_head_in_cm(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _data()
    data["head_circumference"] = {"value": "20", "unit": "in", "provenance": "measured"}
    data["ease"] = {"value": "-2", "unit": "cm", "provenance": "entered"}
    del data["proposed_cast_on"]

    code, out, _ = _run(tmp_path, data, capsys)

    assert code == 0
    assert f"Tour visé   48,8 cm (50,8 {MINUS} 2)" in out
    assert f"(48,8 {TIMES} 20 / 10) → 96 m" in out
