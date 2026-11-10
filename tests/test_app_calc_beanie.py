"""`calc_beanie` : la demande devient un rapport unique (CLA-69)."""

from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from knitproof.app.beanie import calc_beanie
from knitproof.app.errors import InputFileError
from knitproof.domain.gauge import GaugeSource
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
    assert calc.cast_on is not None
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


SWATCH_20 = {"stitches": "20", "width": {"value": "10", "unit": "cm"}}
ROWS_30 = {"rows": "30", "height": {"value": "10", "unit": "cm"}}


def _without_swatch(**extra: object) -> dict[str, object]:
    data = _data()
    del data["swatch"]
    del data["proposed_cast_on"]
    data.update(extra)
    return data


def _swatch_only(**measures: object) -> dict[str, object]:
    data = _data()
    del data["proposed_cast_on"]
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    for key in ("before_blocking", "after_blocking"):
        del swatch[key]
    swatch.update(measures)
    return data


def test_a_blocked_swatch_resolves_to_the_blocked_source() -> None:
    calc = calc_beanie(EXAMPLE)

    assert calc.gauge.source is GaugeSource.BLOCKED
    assert calc.gauge.gauge is not None
    assert calc.gauge.gauge.stitches == Decimal(20)


def test_a_label_without_swatch_gives_a_plan_on_the_label(tmp_path: Path) -> None:
    label = {**SWATCH_20, **ROWS_30}
    calc = calc_beanie(_write(tmp_path, _without_swatch(label_gauge=label)))

    assert calc.gauge.source is GaugeSource.LABEL
    assert calc.report.result is not None
    assert calc.report.result.cast_on == 88
    assert calc.cast_on is not None
    assert calc.cast_on.raw_stitches == Decimal("86.4")
    entry = _entry(calc.report.entries, "gauge_from_label")
    assert entry.lines[0].startswith("À VÉRIFIER : jauge du fabricant, état de blocage inconnu")


def test_a_label_range_without_swatch_asks_which_value_to_keep(tmp_path: Path) -> None:
    label = {"stitches": {"low": "20", "high": "22"}, "width": SWATCH_20["width"]}
    calc = calc_beanie(_write(tmp_path, _without_swatch(label_gauge=label)))

    assert calc.report.result is None
    assert calc.cast_on is None
    assert [question.code for question in calc.report.questions] == ["label_gauge_range"]


def test_neither_swatch_nor_label_asks_and_invents_nothing(tmp_path: Path) -> None:
    calc = calc_beanie(_write(tmp_path, _without_swatch()))

    assert calc.report.result is None
    assert calc.gauge.gauge is None
    assert calc.cast_on is None
    assert [question.code for question in calc.report.questions] == ["gauge_missing"]


def test_an_unknown_blocking_swatch_asks_and_gives_no_plan(tmp_path: Path) -> None:
    calc = calc_beanie(_write(tmp_path, _swatch_only(unknown_blocking={**SWATCH_20, **ROWS_30})))

    assert calc.report.result is None
    assert [question.code for question in calc.report.questions] == ["gauge_blocking_unknown"]
    assert calc.report.questions[0].options == ("oui", "non")


def test_an_unblocked_swatch_alone_is_followed_and_marked_to_verify(tmp_path: Path) -> None:
    calc = calc_beanie(_write(tmp_path, _swatch_only(before_blocking={**SWATCH_20, **ROWS_30})))

    assert calc.gauge.source is GaugeSource.UNBLOCKED
    assert calc.report.result is not None
    assert calc.report.result.cast_on == 88
    entry = _entry(calc.report.entries, "gauge_unblocked")
    assert "bloquer (laver puis sécher)" in " ".join(entry.lines)
    assert "unblocked_swatch_cast_on" not in {e.code for e in calc.report.entries}


def test_the_row_gauge_question_names_the_label_when_it_has_no_rows(tmp_path: Path) -> None:
    calc = calc_beanie(_write(tmp_path, _without_swatch(label_gauge=SWATCH_20)))

    assert calc.report.result is None
    (question,) = calc.report.questions
    assert question.code == "row_gauge_missing"
    assert "étiquette" in question.text
    assert "après blocage" not in question.text


def test_a_swatch_and_a_label_far_apart_warn_and_the_plan_follows_the_swatch(
    tmp_path: Path,
) -> None:
    data = _data()
    data["label_gauge"] = {"stitches": "24", "width": SWATCH_20["width"]}

    calc = calc_beanie(_write(tmp_path, data))

    assert calc.report.result is not None
    assert calc.report.result.cast_on == 88
    entry = _entry(calc.report.entries, "gauge_differs_from_label")
    assert entry.status is ReportStatus.WARNING
    assert "aiguilles plus fines" in " ".join(entry.lines)


def test_a_swatch_and_a_close_label_give_no_gap_notice(tmp_path: Path) -> None:
    data = _data()
    data["label_gauge"] = {"stitches": "21", "width": SWATCH_20["width"]}

    calc = calc_beanie(_write(tmp_path, data))

    assert "gauge_differs_from_label" not in {entry.code for entry in calc.report.entries}


def test_the_proposed_cast_on_is_checked_against_the_resolved_gauge(tmp_path: Path) -> None:
    label = {**SWATCH_20, **ROWS_30}
    data = _without_swatch(label_gauge=label)
    data["proposed_cast_on"] = {"stitches": 120, "origin": "llm_only"}

    calc = calc_beanie(_write(tmp_path, data))

    entry = _entry(calc.report.entries, "differs_from_calculation")
    assert entry.status is ReportStatus.REJECTED
    assert entry.lines[-1].startswith("Avec la jauge de l’étiquette, 120 m donnent")


def test_without_a_swatch_the_needles_are_not_compared(tmp_path: Path) -> None:
    label = {**SWATCH_20, **ROWS_30}
    calc = calc_beanie(_write(tmp_path, _without_swatch(label_gauge=label)))

    assert "swatch_needle_mismatch" not in {entry.code for entry in calc.report.entries}
