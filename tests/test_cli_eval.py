"""`knitproof eval` : tableau k/N, résultat daté, codes de sortie, sans réseau (CLA-188)."""

import datetime
import os
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel
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
    "OPENROUTER_API_KEY": "fausse",
    "KNITPROOF_OPENROUTER_TEMPERATURE": "0",
    "KNITPROOF_LLM_RETRIES": "0",
    "KNITPROOF_LLM_HTTP_RETRIES": "0",
    "KNITPROOF_LLM_HTTP_WAIT": "0",
}


_READING: dict[str, object] = {
    "head_circumference": {"value": 48, "unit": "cm"},
    "smaller_than_head": {"value": 5, "unit": "cm"},
    "gauge_after_blocking": {"stitches": 20, "width": {"value": 10, "unit": "cm"}},
    "edge": "rib_2x2",
}


def _reading_reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart("final_result", _READING)])


def _agent_for[T: BaseModel](
    config: ModelConfig,
    output_type: type[T],
    baseline: Callable[[Sequence[ModelMessage], AgentInfo], ModelResponse],
) -> Agent[None, T]:
    """Un agent de test : `baseline` répond au calcul du « LLM seul », la lecture est fixe."""
    reply = baseline if output_type is CastOnAnswer else _reading_reply
    return agent_on(FunctionModel(reply), output_type, config.retries)


def _install(monkeypatch: pytest.MonkeyPatch, *, stitches: int | None, fail: bool = False) -> None:
    def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        if fail:
            raise ModelHTTPError(400, "claude", body="temperature is not supported")
        return ModelResponse(parts=[ToolCallPart("final_result", {"stitches": stitches})])

    def factory[T: BaseModel](config: ModelConfig, output_type: type[T]) -> Agent[None, T]:
        return _agent_for(config, output_type, reply)

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


def test_two_openrouter_entries_are_wired_with_their_hosts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)
    models = "openrouter:mistralai/m@mistral/eu,openrouter:moonshotai/k@moonshotai"

    code = main(["eval", "--split", "dev", "--models", models, "--results", str(tmp_path)])

    out = capsys.readouterr().out
    written = list(tmp_path.glob("*-dev.yaml"))
    saved = yaml.safe_load(written[0].read_text(encoding="utf-8"))
    assert code == 0
    assert out.count("/18") == 2
    assert [(item["model"], item["host"]) for item in saved["providers"]] == [
        ("mistralai/m", "mistral/eu"),
        ("moonshotai/k", "moonshotai"),
    ]


def test_a_model_given_in_the_entry_reaches_the_agent_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch, stitches=88)
    seen: list[ModelConfig] = []

    def factory[T: BaseModel](config: ModelConfig, output_type: type[T]) -> Agent[None, T]:
        seen.append(config)
        return _agent_for(
            config,
            output_type,
            lambda messages, info: ModelResponse(
                parts=[ToolCallPart("final_result", {"stitches": 88})]
            ),
        )

    monkeypatch.setattr("knitproof.app.baseline.build_agent", factory)

    code = main(
        ["eval", "--split", "dev", "--models", "ollama:llama3.2:3b", "--results", str(tmp_path)]
    )

    assert code == 0
    assert {config.model for config in seen} == {"llama3.2:3b"}


def test_malformed_entries_exit_3_naming_the_entry_without_a_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)

    for entry in ("ollama:", "openrouter:x@", "anthropic@x"):
        code = main(["eval", "--split", "dev", "--models", entry, "--results", str(tmp_path)])

        assert code == 3
        assert entry in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


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


def _install_failing(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[int],
    error: ModelHTTPError,
    *,
    times: int | None,
) -> None:
    """Un modèle qui lève `error` aux `times` premiers appels (`None` : toujours), puis répond."""

    def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        if times is None or len(calls) <= times:
            raise error
        return ModelResponse(parts=[ToolCallPart("final_result", {"stitches": 88})])

    def factory[T: BaseModel](config: ModelConfig, output_type: type[T]) -> Agent[None, T]:
        return _agent_for(config, output_type, reply)

    environ = {**ENVIRONMENT, "KNITPROOF_LLM_HTTP_RETRIES": "2", "KNITPROOF_LLM_HTTP_WAIT": "0"}
    monkeypatch.setattr("knitproof.app.baseline.build_agent", factory)
    monkeypatch.setattr(os, "environ", environ)


def test_a_passing_429_is_retried_and_the_measure_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []
    _install_failing(monkeypatch, calls, ModelHTTPError(429, "claude", body="limite"), times=1)

    code = main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])

    written = list(tmp_path.glob("*-dev.yaml"))
    saved = yaml.safe_load(written[0].read_text(encoding="utf-8"))
    attempts = [run["run"]["attempts"] for run in saved["providers"][0]["runs"]]
    assert code == 0
    assert attempts[0] == 2
    assert set(attempts[1:]) == {1}
    assert len(calls) == 19


def test_an_endless_429_exits_3_naming_the_attempts_without_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[int] = []
    _install_failing(monkeypatch, calls, ModelHTTPError(429, "claude", body="limite"), times=None)

    code = main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])

    assert code == 3
    err = capsys.readouterr().err
    assert "ollama" in err
    assert "3 essai" in err
    assert list(tmp_path.iterdir()) == []
    assert len(calls) == 3


def test_an_exhausted_quota_exits_3_naming_the_provider_without_a_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[int] = []
    body = {
        "error": {
            "type": "rate_limit_error",
            "details": {"error_code": "enforced_spend_limit_reached"},
        }
    }
    _install_failing(monkeypatch, calls, ModelHTTPError(429, "claude", body=body), times=None)

    code = main(["eval", "--split", "dev", "--models", "anthropic", "--results", str(tmp_path)])

    assert code == 3
    err = capsys.readouterr().err
    assert "anthropic" in err
    assert "quota épuisé" in err
    assert list(tmp_path.glob("*.yaml")) == []
    assert len(calls) == 1


def test_a_400_exits_3_after_a_single_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    _install_failing(monkeypatch, calls, ModelHTTPError(400, "claude", body="refusé"), times=None)

    code = main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])

    assert code == 3
    assert list(tmp_path.iterdir()) == []
    assert len(calls) == 1


def test_an_unknown_provider_exits_3_and_lists_the_known_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, stitches=88)

    code = main(["eval", "--split", "dev", "--models", "gemini", "--results", str(tmp_path)])

    assert code == 3
    assert "anthropic" in capsys.readouterr().err


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


def _install_failing_at(
    monkeypatch: pytest.MonkeyPatch, calls: list[int], stop: int | None
) -> None:
    """Un modèle qui répond 88, sauf au `stop`-ième appel où le fournisseur refuse (400)."""

    def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        if len(calls) == stop:
            raise ModelHTTPError(400, "claude", body="refusé")
        return ModelResponse(parts=[ToolCallPart("final_result", {"stitches": 88})])

    def factory[T: BaseModel](config: ModelConfig, output_type: type[T]) -> Agent[None, T]:
        return _agent_for(config, output_type, reply)

    monkeypatch.setattr("knitproof.app.baseline.build_agent", factory)
    monkeypatch.setattr(os, "environ", dict(ENVIRONMENT))


def test_a_stopped_measure_keeps_its_journal_and_a_resume_finishes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[int] = []
    _install_failing_at(monkeypatch, calls, stop=2)
    args = ["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)]

    assert main(args) == 3

    (journal,) = tmp_path.glob("*-dev.partial.jsonl")
    assert str(journal) in capsys.readouterr().err
    assert list(tmp_path.glob("*.yaml")) == []

    calls.clear()
    _install_failing_at(monkeypatch, calls, stop=None)
    code = main([*args, "--resume", str(journal)])

    out = capsys.readouterr().out
    assert code == 0
    assert len(calls) == 17  # 18 passages, 1 acquis
    assert len(list(tmp_path.glob("*-dev.yaml"))) == 1
    assert list(tmp_path.glob("*.partial.jsonl")) == []
    assert "0/18" not in out


def test_the_stop_message_names_the_resume_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_failing_at(monkeypatch, [], stop=2)

    main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])

    (journal,) = tmp_path.glob("*.partial.jsonl")
    assert f"reprise : --resume {journal}" in capsys.readouterr().err


def test_a_journal_of_other_models_exits_3_naming_the_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[int] = []
    _install_failing_at(monkeypatch, calls, stop=2)
    main(["eval", "--split", "dev", "--models", "ollama", "--results", str(tmp_path)])
    (journal,) = tmp_path.glob("*.partial.jsonl")
    capsys.readouterr()
    calls.clear()
    _install_failing_at(monkeypatch, calls, stop=None)

    code = main(
        [
            "eval",
            "--split",
            "dev",
            "--models",
            "anthropic,ollama",
            "--results",
            str(tmp_path),
            "--resume",
            str(journal),
        ]
    )

    assert code == 3
    assert "entries" in capsys.readouterr().err
    assert calls == []
    assert journal.exists()
