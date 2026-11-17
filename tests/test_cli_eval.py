"""`knitproof eval` : tableau k/N, résultat daté, codes de sortie, sans réseau (CLA-188)."""

import datetime
import os
from collections.abc import Sequence
from pathlib import Path

import pytest
import yaml
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from knitproof.app.baseline import CastOnAnswer
from knitproof.cli.main import main
from knitproof.llm.agents import agent_on
from knitproof.llm.config import ModelConfig

ENVIRONMENT = {
    "ANTHROPIC_API_KEY": "fausse",
    "KNITPROOF_ANTHROPIC_MODEL": "claude-sonnet-5-5-20261001",
    "KNITPROOF_ANTHROPIC_TEMPERATURE": "omit",
    "KNITPROOF_OLLAMA_MODEL": "qwen3:8b",
    "KNITPROOF_OLLAMA_BASE_URL": "http://localhost:11434/v1",
    "KNITPROOF_OLLAMA_TEMPERATURE": "0",
    "KNITPROOF_LLM_RETRIES": "0",
}


def _install(monkeypatch: pytest.MonkeyPatch, *, stitches: int | None, fail: bool = False) -> None:
    def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        if fail:
            raise ModelHTTPError(400, "claude", body="temperature is not supported")
        return ModelResponse(parts=[ToolCallPart("final_result", {"stitches": stitches})])

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        return agent_on(FunctionModel(reply), CastOnAnswer, config.retries)

    monkeypatch.setattr("knitproof.app.baseline.build_agent", factory)
    monkeypatch.setattr(os, "environ", dict(ENVIRONMENT))


def test_one_line_per_model_and_a_dated_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)

    code = main(
        ["eval", "--split", "dev", "--models", "anthropic,ollama", "--results", str(tmp_path)]
    )

    out = capsys.readouterr().out
    written = list(tmp_path.glob("*-dev.yaml"))
    assert code == 0
    assert len(written) == 1
    assert "anthropic" in out
    assert "ollama" in out
    assert out.count("/18") == 2  # 6 cas dev, 3 passages
    assert str(written[0]) in out
    saved = yaml.safe_load(written[0].read_text(encoding="utf-8"))
    assert [item["provider"] for item in saved["providers"]] == ["anthropic", "ollama"]
    assert saved["passes"] == 3


def test_an_abstaining_model_is_shown_with_its_abstentions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=None)

    code = main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 0
    assert out.count("0/18") == 1
    assert "abstentions : 18" in out


def test_an_invalid_configuration_exits_3_without_a_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)
    monkeypatch.setattr(os, "environ", {})

    code = main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])

    captured = capsys.readouterr()
    assert code == 3
    assert "KNITPROOF_OLLAMA_BASE_URL" in captured.err
    assert captured.out == ""
    assert list(tmp_path.iterdir()) == []


def test_a_provider_http_error_exits_3_without_a_partial_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88, fail=True)

    code = main(["eval", "--split", "dev", "--models", "anthropic", "--results", str(tmp_path)])

    assert code == 3
    assert "anthropic" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_an_unknown_provider_exits_3_and_lists_the_known_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)

    code = main(["eval", "--split", "dev", "--models", "gemini", "--results", str(tmp_path)])

    assert code == 3
    assert "anthropic" in capsys.readouterr().err


def test_an_empty_test_split_exits_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)

    code = main(["eval", "--split", "test", "--models", "ollama", "--results", str(tmp_path)])

    assert code == 3
    assert "aucun cas" in capsys.readouterr().err


def test_a_result_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)
    fixed = datetime.datetime(2026, 11, 17, 9, 30, tzinfo=datetime.UTC)
    monkeypatch.setattr("knitproof.cli.main._now", lambda: fixed)
    args = ["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)]

    assert main(args) == 0
    capsys.readouterr()
    code = main(args)

    assert code == 3
    assert "existe déjà" in capsys.readouterr().err
