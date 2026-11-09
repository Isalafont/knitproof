"""`calc_beanie` : la demande devient un rapport unique (CLA-69)."""

from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from knitproof.app.beanie import calc_beanie
from knitproof.app.errors import InputFileError
from knitproof.domain.report import ReportEntry, ReportStatus

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "bonnet-3-ans.yaml"


def _data() -> dict[str, object]:
    loaded = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _write(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "demande.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def _entry(entries: tuple[ReportEntry, ...], code: str) -> ReportEntry:
    (found,) = [entry for entry in entries if entry.code == code]
    return found


def test_the_example_casts_on_88_with_the_raw_count_and_the_finished_width() -> None:
    calc = calc_beanie(EXAMPLE)

    assert calc.report.result is not None
    assert calc.report.result.cast_on == 88
    assert calc.cast_on.raw_stitches == Decimal("86.4")
    assert calc.cast_on.finished_cm == Decimal(44)


def test_the_unblocked_swatch_warns_with_96_stitches_and_48_cm() -> None:
    calc = calc_beanie(EXAMPLE)

    entry = _entry(calc.report.entries, "unblocked_swatch_cast_on")

    assert entry.status is ReportStatus.WARNING
    assert entry.lines == (
        "Avec l’échantillon avant blocage (22 m), on monterait 96 m.",
        "96 m donneraient 48 cm après blocage, sans aisance.",
    )


def test_the_llm_proposal_is_rejected_with_60_cm() -> None:
    calc = calc_beanie(EXAMPLE)

    entry = _entry(calc.report.entries, "differs_from_calculation")

    assert entry.status is ReportStatus.REJECTED
    assert entry.lines[0] == "Proposition d’un LLM seul : 120 m"
    assert any("120 m donnent 60 cm" in line for line in entry.lines)


def test_the_needle_text_is_the_millimetre_size_and_nothing_to_report() -> None:
    calc = calc_beanie(EXAMPLE)

    assert [info.text for info in calc.needles] == ["4 mm"]
    assert {entry.code for entry in calc.report.entries} == {
        "unblocked_swatch_cast_on",
        "differs_from_calculation",
    }


def test_an_unknown_us_needle_gives_a_warning(tmp_path: Path) -> None:
    data = {**_data(), "needles": [{"size": "US 99", "kind": "double_pointed"}]}

    calc = calc_beanie(_write(tmp_path, data))

    entry = _entry(calc.report.entries, "unknown_needle_size")
    assert entry.status is ReportStatus.WARNING


def test_without_unblocked_swatch_nor_proposal_there_is_no_alert_nor_rejection(
    tmp_path: Path,
) -> None:
    data = _data()
    del data["proposed_cast_on"]
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    del swatch["before_blocking"]

    calc = calc_beanie(_write(tmp_path, data))

    assert calc.report.entries == ()


def test_without_row_gauge_there_is_no_plan_but_questions(tmp_path: Path) -> None:
    data = _data()
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    swatch["after_blocking"] = {"stitches": "20", "width": {"value": "10", "unit": "cm"}}

    calc = calc_beanie(_write(tmp_path, data))

    assert calc.report.result is None
    assert calc.report.questions


@pytest.mark.parametrize("where", ["stitches", "proposed"])
def test_a_27_digit_integer_is_too_big_without_trace(tmp_path: Path, where: str) -> None:
    data = _data()
    if where == "proposed":
        data["proposed_cast_on"] = {"stitches": 10**27, "origin": "llm_only"}
    else:
        data["stitch_multiple"] = {
            "repeat_multiple": 10**27,
            "repeat_offset": 0,
            "provenance": "entered",
        }

    with pytest.raises(InputFileError) as raised:
        calc_beanie(_write(tmp_path, data))

    assert "trop grand" in raised.value.reason
    assert "Traceback" not in str(raised.value)


def test_matching_swatches_give_no_unblocked_alert(tmp_path: Path) -> None:
    data = _data()
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    swatch["before_blocking"] = dict(swatch["after_blocking"])

    calc = calc_beanie(_write(tmp_path, data))

    assert "unblocked_swatch_cast_on" not in {entry.code for entry in calc.report.entries}
