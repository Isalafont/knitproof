"""Le journal JSON Lines des passages d’une mesure (CLA-203)."""

import datetime
import os
from decimal import Decimal
from pathlib import Path

import pytest

from knitproof.app.baseline_journal import (
    CaseHash,
    EntryIdentity,
    Journal,
    JournalError,
    JournalHeader,
)
from knitproof.app.baseline_models import BaselineRun, CastOnAnswer, ModelRun, Verdict
from knitproof.app.eval_cases import Split
from knitproof.domain.reading import ModelReading

MEASURED_ON = datetime.datetime(
    2026, 11, 18, 9, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=1))
)
SHA = "a" * 64
IDENTITY = EntryIdentity(provider="ollama", model="qwen3:8b", host=None)
OTHER = EntryIdentity(provider="openrouter", model="x", host="a")


def _header(**changes: object) -> JournalHeader:
    fields: dict[str, object] = {
        "split": Split.DEV,
        "prompt_sha256": SHA,
        "passes": 3,
        "measured_on": MEASURED_ON,
        "cases": (CaseHash(case_id="c1", sha256="b" * 64), CaseHash(case_id="c2", sha256="c" * 64)),
        "entries": (IDENTITY, OTHER),
    }
    return JournalHeader.model_validate({**fields, **changes})


def _run(case_id: str = "c1", attempt: int = 1, *, reading: bool = True) -> BaselineRun:
    seen = (
        ModelReading(
            provider="ollama",
            model="qwen3:8b",
            model_version="qwen3:8b",
            prompt_id="p",
            prompt_sha256=SHA,
        )
        if reading
        else None
    )
    return BaselineRun(
        case_id=case_id,
        attempt=attempt,
        answer=CastOnAnswer(stitches=88),
        rejection=None,
        finished_cm=Decimal("55.0000000000000000000000001"),
        verdict=Verdict.CORRECT,
        run=ModelRun(
            provider="ollama",
            model="qwen3:8b",
            prompt_id="p",
            prompt_sha256=SHA,
            reading=seen,
            temperature=0.0,
            output_mode="tool",
            input_tokens=51,
            output_tokens=4,
            latency_ms=500,
            attempts=1,
            at=MEASURED_ON,
        ),
    )


def test_the_first_line_is_the_header_and_each_run_adds_a_line(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    journal = Journal.start(path, _header())

    assert not path.exists()
    journal.record(IDENTITY, _run("c1", 1))
    journal.record(IDENTITY, _run("c1", 2))

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    assert text.endswith("\n")
    assert len(lines) == 4
    assert JournalHeader.model_validate_json(lines[0]) == _header()


def test_start_refuses_an_existing_journal(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    path.write_text("", encoding="utf-8")

    with pytest.raises(JournalError, match="existe déjà"):
        Journal.start(path, _header())


def test_resume_gives_back_the_runs_written(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    journal = Journal.start(path, _header())
    written = _run("c2", 3)
    journal.record(IDENTITY, written)
    journal.record(OTHER, _run("c1", 1, reading=False))

    resumed = Journal.resume(path, _header())

    assert resumed.recorded(IDENTITY, "c2", 3) == written
    assert resumed.recorded(IDENTITY, "c2", 1) is None
    assert resumed.recorded(OTHER, "c2", 3) is None
    assert resumed.recorded(OTHER, "c1", 1) == _run("c1", 1, reading=False)


def test_the_header_of_a_journal_can_be_read(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    Journal.start(path, _header()).record(IDENTITY, _run())

    assert Journal.read_header(path) == _header()


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"prompt_sha256": "d" * 64}, "prompt_sha256"),
        ({"passes": 5}, "passes"),
        ({"split": Split.TEST}, "split"),
        ({"cases": (CaseHash(case_id="c1", sha256="e" * 64),)}, "cases"),
        ({"entries": (IDENTITY,)}, "entries"),
        (
            {"entries": (IDENTITY, EntryIdentity(provider="openrouter", model="x", host="b"))},
            "entries",
        ),
    ],
)
def test_resume_refuses_a_different_header_naming_the_field(
    tmp_path: Path, changes: dict[str, object], field: str
) -> None:
    path = tmp_path / "j.partial.jsonl"
    Journal.start(path, _header()).record(IDENTITY, _run())

    with pytest.raises(JournalError, match=field):
        Journal.resume(path, _header(**changes))


def test_resume_does_not_compare_the_date_of_the_first_launch(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    Journal.start(path, _header()).record(IDENTITY, _run())
    later = MEASURED_ON + datetime.timedelta(days=1)

    resumed = Journal.resume(path, _header(measured_on=later))

    assert resumed.recorded(IDENTITY, "c1", 1) == _run()


def test_resume_refuses_a_missing_journal(tmp_path: Path) -> None:
    with pytest.raises(JournalError, match="introuvable"):
        Journal.resume(tmp_path / "absent.partial.jsonl", _header())


@pytest.mark.parametrize("tail", ['{"identity": {"provider": "oll', "pas du json"])
def test_an_unfinished_last_line_is_ignored_and_cut_before_any_append(
    tmp_path: Path, tail: str
) -> None:
    path = tmp_path / "j.partial.jsonl"
    journal = Journal.start(path, _header())
    journal.record(IDENTITY, _run("c1", 1))
    journal.record(IDENTITY, _run("c1", 2))
    valid = path.read_bytes()
    path.write_bytes(valid + tail.encode("utf-8"))

    resumed = Journal.resume(path, _header())

    assert path.read_bytes() == valid
    assert resumed.recorded(IDENTITY, "c1", 2) == _run("c1", 2)
    resumed.record(IDENTITY, _run("c1", 3))
    assert Journal.resume(path, _header()).recorded(IDENTITY, "c1", 3) == _run("c1", 3)


def test_an_unreadable_finished_last_line_is_ignored_too(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    journal = Journal.start(path, _header())
    journal.record(IDENTITY, _run("c1", 1))
    valid = path.read_bytes()
    path.write_bytes(valid + b"pas du json\n")

    resumed = Journal.resume(path, _header())

    assert path.read_bytes() == valid
    assert resumed.recorded(IDENTITY, "c1", 1) == _run("c1", 1)


def test_an_unreadable_line_in_the_middle_refuses_the_resume(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    journal = Journal.start(path, _header())
    journal.record(IDENTITY, _run("c1", 1))
    journal.record(IDENTITY, _run("c1", 2))
    head, first, second = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([head, "pas du json", second]) + "\n", encoding="utf-8")

    with pytest.raises(JournalError, match="ligne 2"):
        Journal.resume(path, _header())
    assert first


def test_an_unreadable_header_refuses_the_resume(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    path.write_text("pas du json\n", encoding="utf-8")

    with pytest.raises(JournalError, match="en-tête"):
        Journal.resume(path, _header())


def test_discard_removes_the_file_and_tolerates_its_absence(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    journal = Journal.start(path, _header())
    journal.record(IDENTITY, _run())

    journal.discard()
    journal.discard()

    assert not path.exists()


def test_a_journal_cut_inside_its_header_tells_to_delete_it_and_relaunch(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    path.write_text(_header().model_dump_json()[:40], encoding="utf-8")

    with pytest.raises(JournalError, match=r"supprimer le journal.*sans --resume"):
        Journal.resume(path, _header())


def test_the_header_is_written_alone_before_the_first_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "j.partial.jsonl"
    seen: list[str] = []
    real = os.fsync

    def spy(descriptor: int) -> None:
        seen.append(path.read_text(encoding="utf-8"))
        real(descriptor)

    monkeypatch.setattr("knitproof.app.baseline_journal.os.fsync", spy)

    Journal.start(path, _header()).record(IDENTITY, _run())

    assert len(seen) == 2
    assert seen[0].count("\n") == 1  # l’en-tête seul est sur disque avant le passage
    assert seen[1].count("\n") == 2


def test_a_refusal_on_entries_shows_them_as_provider_model_host(tmp_path: Path) -> None:
    path = tmp_path / "j.partial.jsonl"
    Journal.start(path, _header()).record(IDENTITY, _run())
    reversed_entries = (OTHER, IDENTITY)

    with pytest.raises(JournalError) as raised:
        Journal.resume(path, _header(entries=reversed_entries))

    message = str(raised.value)
    assert "ollama:qwen3:8b, openrouter:x@a" in message
    assert "openrouter:x@a, ollama:qwen3:8b" in message
    assert "EntryIdentity" not in message
