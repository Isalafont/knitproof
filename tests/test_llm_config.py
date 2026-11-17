"""La configuration des modèles est lue dans l’environnement (CLA-127, ADR 0033)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from knitproof.llm.config import ModelConfig, Provider, load_config
from knitproof.llm.errors import InvalidSettingError, LlmError, MissingSettingError

KEY = "cle-secrete-de-test"
ENVIRONMENTS: dict[Provider, dict[str, str]] = {
    "anthropic": {
        "ANTHROPIC_API_KEY": KEY,
        "KNITPROOF_ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929",
        "KNITPROOF_LLM_RETRIES": "1",
    },
    "mistral": {
        "MISTRAL_API_KEY": KEY,
        "KNITPROOF_MISTRAL_MODEL": "mistral-small-2506",
        "KNITPROOF_LLM_RETRIES": "1",
    },
    "openai": {
        "OPENAI_API_KEY": KEY,
        "KNITPROOF_OPENAI_MODEL": "gpt-5-2025-08-07",
        "KNITPROOF_LLM_RETRIES": "1",
    },
    "openrouter": {
        "OPENROUTER_API_KEY": KEY,
        "KNITPROOF_OPENROUTER_MODEL": "mistralai/mistral-small-2506",
        "KNITPROOF_OPENROUTER_HOST": "mistral",
        "KNITPROOF_LLM_RETRIES": "1",
    },
    "moonshotai": {
        "MOONSHOTAI_API_KEY": KEY,
        "KNITPROOF_MOONSHOTAI_MODEL": "kimi-k3",
        "KNITPROOF_LLM_RETRIES": "1",
    },
    "ollama": {
        "KNITPROOF_OLLAMA_MODEL": "qwen3:8b-q4_K_M",
        "KNITPROOF_OLLAMA_BASE_URL": "http://localhost:11434/v1",
        "KNITPROOF_LLM_RETRIES": "1",
    },
}


def environ(provider: Provider, **changes: str | None) -> dict[str, str]:
    values = dict(ENVIRONMENTS[provider])
    for name, value in changes.items():
        if value is None:
            values.pop(name, None)
        else:
            values[name] = value
    return values


@pytest.mark.parametrize("provider", ["anthropic", "mistral", "openai", "openrouter", "moonshotai"])
def test_a_complete_environment_gives_a_config(provider: Provider) -> None:
    config = load_config(provider, ENVIRONMENTS[provider])

    assert config.provider == provider
    assert config.model == ENVIRONMENTS[provider][f"KNITPROOF_{provider.upper()}_MODEL"]
    assert config.api_key is not None
    assert config.api_key.get_secret_value() == KEY
    assert config.base_url is None
    assert config.temperature is None
    assert config.retries == 1


@pytest.mark.parametrize(
    ("provider", "variable"),
    [
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("anthropic", "KNITPROOF_ANTHROPIC_MODEL"),
        ("anthropic", "KNITPROOF_LLM_RETRIES"),
        ("mistral", "MISTRAL_API_KEY"),
        ("mistral", "KNITPROOF_MISTRAL_MODEL"),
        ("mistral", "KNITPROOF_LLM_RETRIES"),
        ("openai", "OPENAI_API_KEY"),
        ("openai", "KNITPROOF_OPENAI_MODEL"),
        ("openrouter", "OPENROUTER_API_KEY"),
        ("openrouter", "KNITPROOF_OPENROUTER_MODEL"),
        ("openrouter", "KNITPROOF_OPENROUTER_HOST"),
        ("moonshotai", "MOONSHOTAI_API_KEY"),
        ("moonshotai", "KNITPROOF_MOONSHOTAI_MODEL"),
        ("ollama", "KNITPROOF_OLLAMA_MODEL"),
        ("ollama", "KNITPROOF_OLLAMA_BASE_URL"),
        ("ollama", "KNITPROOF_LLM_RETRIES"),
    ],
)
def test_a_missing_variable_is_named(provider: Provider, variable: str) -> None:
    with pytest.raises(MissingSettingError, match=variable) as raised:
        load_config(provider, environ(provider, **{variable: None}))

    assert raised.value.variable == variable


def test_an_empty_variable_counts_as_missing() -> None:
    with pytest.raises(MissingSettingError, match="ANTHROPIC_API_KEY"):
        load_config("anthropic", environ("anthropic", ANTHROPIC_API_KEY=""))


def test_a_local_model_needs_no_key() -> None:
    config = load_config("ollama", ENVIRONMENTS["ollama"])

    assert config.api_key is None
    assert config.base_url == "http://localhost:11434/v1"
    assert config.model == "qwen3:8b-q4_K_M"


@pytest.mark.parametrize("model", ["qwen3:latest", "qwen3:LATEST", "qwen3"])
def test_a_local_model_without_an_explicit_tag_is_refused(model: str) -> None:
    with pytest.raises(InvalidSettingError, match="KNITPROOF_OLLAMA_MODEL"):
        load_config("ollama", environ("ollama", KNITPROOF_OLLAMA_MODEL=model))


def test_an_empty_openrouter_host_is_named() -> None:
    with pytest.raises(MissingSettingError, match="KNITPROOF_OPENROUTER_HOST"):
        load_config("openrouter", environ("openrouter", KNITPROOF_OPENROUTER_HOST="  "))


def test_the_openrouter_host_is_kept() -> None:
    assert load_config("openrouter", ENVIRONMENTS["openrouter"]).host == "mistral"


def test_only_openrouter_has_a_host() -> None:
    assert load_config("mistral", ENVIRONMENTS["mistral"]).host is None


def test_an_openrouter_base_url_is_refused() -> None:
    with pytest.raises(InvalidSettingError, match="KNITPROOF_OPENROUTER_BASE_URL"):
        load_config(
            "openrouter",
            environ("openrouter", KNITPROOF_OPENROUTER_BASE_URL="https://exemple.test/v1"),
        )


def test_the_other_provider_variables_are_not_required() -> None:
    config = load_config("mistral", ENVIRONMENTS["mistral"])

    assert config.provider == "mistral"


@pytest.mark.parametrize(
    ("provider", "variable"),
    [
        ("anthropic", "KNITPROOF_ANTHROPIC_MODEL"),
        ("mistral", "KNITPROOF_MISTRAL_MODEL"),
        ("openai", "KNITPROOF_OPENAI_MODEL"),
        ("openrouter", "KNITPROOF_OPENROUTER_MODEL"),
        ("moonshotai", "KNITPROOF_MOONSHOTAI_MODEL"),
    ],
)
@pytest.mark.parametrize(
    "model", ["claude-sonnet-latest", "mistral-small-LATEST", "x-Latest", "kimi-latest"]
)
def test_a_latest_alias_is_refused(provider: Provider, variable: str, model: str) -> None:
    with pytest.raises(InvalidSettingError, match=variable):
        load_config(provider, environ(provider, **{variable: model}))


@pytest.mark.parametrize("temperature", ["-0.1", "1.1", "chaud", "nan"])
def test_a_temperature_out_of_range_or_not_a_number_is_refused(temperature: str) -> None:
    with pytest.raises(InvalidSettingError, match="KNITPROOF_LLM_TEMPERATURE"):
        load_config("anthropic", environ("anthropic", KNITPROOF_LLM_TEMPERATURE=temperature))


@pytest.mark.parametrize(("text", "value"), [("0", 0.0), ("0.5", 0.5), ("1", 1.0)])
def test_a_temperature_between_zero_and_one_is_kept(text: str, value: float) -> None:
    config = load_config("anthropic", environ("anthropic", KNITPROOF_LLM_TEMPERATURE=text))

    assert config.temperature == value


@pytest.mark.parametrize("retries", ["-1", "deux", "1.5", "1_0", "+1"])
def test_invalid_retries_are_refused(retries: str) -> None:
    with pytest.raises(InvalidSettingError, match="KNITPROOF_LLM_RETRIES"):
        load_config("anthropic", environ("anthropic", KNITPROOF_LLM_RETRIES=retries))


def test_zero_retries_are_accepted() -> None:
    config = load_config("anthropic", environ("anthropic", KNITPROOF_LLM_RETRIES="0"))

    assert config.retries == 0


def test_an_unknown_provider_is_refused() -> None:
    with pytest.raises(InvalidSettingError, match="provider"):
        load_config("cohere", {})  # type: ignore[arg-type]


def test_a_base_url_is_read_when_present() -> None:
    config = load_config(
        "mistral", environ("mistral", KNITPROOF_MISTRAL_BASE_URL="https://exemple.test/v1")
    )

    assert config.base_url == "https://exemple.test/v1"


def test_the_key_appears_neither_in_the_repr_nor_in_an_error() -> None:
    config: ModelConfig = load_config("anthropic", ENVIRONMENTS["anthropic"])
    assert KEY not in repr(config)
    assert KEY not in str(config)

    with pytest.raises(LlmError) as raised:
        load_config("anthropic", environ("anthropic", KNITPROOF_LLM_RETRIES="x"))
    assert KEY not in str(raised.value)


def test_a_failing_live_test_never_prints_the_key() -> None:
    project = Path(__file__).resolve().parents[1]
    secret = "cle-reconnaissable-0123456789"
    env = {
        "ANTHROPIC_API_KEY": secret,
        "KNITPROOF_ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929",
        "PATH": os.environ.get("PATH", ""),
    }

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_llm_live.py", "-m", "live", "-k", "anthropic"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "KNITPROOF_LLM_RETRIES" in output
    assert secret not in output
    assert secret[:8] not in output
