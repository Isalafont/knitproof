"""L’appel de sortie structurée et sa trace (CLA-127, ADR 0033)."""

import hashlib
from collections.abc import Sequence

import pytest
from pydantic import BaseModel, SecretStr
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from knitproof.llm.agents import agent_for, agent_on
from knitproof.llm.config import ModelConfig, Provider
from knitproof.llm.errors import ExtractionRejectedError
from knitproof.llm.extract import Prompt, extract, reading_from

PROMPT = Prompt(id="sample-v1", text="Rends la marque et le poids du texte.")


LOCAL_URL = "http://localhost:11434/v1"
MODELS: dict[Provider, str] = {"openrouter": "vendeur/modele-fige-1", "ollama": "modele:8b"}


class Sample(BaseModel):
    brand: str
    grams: int


def config(
    *,
    temperature: float | None = None,
    retries: int = 0,
    provider: Provider = "anthropic",
    base_url: str | None = None,
    host: str | None = None,
) -> ModelConfig:
    local = provider == "ollama"
    return ModelConfig(
        provider=provider,
        model=MODELS.get(provider, "modele-fige-1"),
        api_key=None if local else SecretStr("fausse"),
        base_url=base_url or (LOCAL_URL if local else None),
        host=host,
        temperature=temperature,
        retries=retries,
    )


def answer(arguments: dict[str, object]) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart("final_result", arguments)])


def test_real_requests_are_blocked() -> None:
    model = AnthropicModel("claude-sonnet-4-5", provider=AnthropicProvider(api_key="fake"))
    agent = Agent(model)
    with pytest.raises(RuntimeError, match="Model requests are not allowed"):
        agent.run_sync("bonjour")


def test_a_test_model_returns_a_validated_object() -> None:
    agent = agent_on(TestModel(), Sample, retries=0)

    extraction = extract(agent, config(), PROMPT, "Drops, 50 g")

    assert isinstance(extraction.value, Sample)


def test_an_output_off_schema_is_rejected() -> None:
    def off_schema(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer({"brand": "Drops", "grams": "pas un nombre"})

    agent = agent_on(FunctionModel(off_schema), Sample, retries=0)

    with pytest.raises(ExtractionRejectedError):
        extract(agent, config(), PROMPT, "Drops, 50 g")


def test_one_output_retry_is_allowed() -> None:
    calls: list[int] = []

    def fails_once(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        if len(calls) == 1:
            return answer({"brand": "Drops", "grams": "pas un nombre"})
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(fails_once), Sample, retries=1)

    extraction = extract(agent, config(retries=1), PROMPT, "Drops, 50 g")

    assert extraction.value == Sample(brand="Drops", grams=50)
    assert len(calls) == 2


@pytest.mark.parametrize("retries", [0, 1])
def test_the_output_retry_budget_is_exact(retries: int) -> None:
    calls: list[int] = []

    def always_off(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        return answer({"brand": "Drops", "grams": "pas un nombre"})

    agent = agent_on(FunctionModel(always_off), Sample, retries=retries)

    with pytest.raises(ExtractionRejectedError):
        extract(agent, config(retries=retries), PROMPT, "Drops, 50 g")

    assert len(calls) == retries + 1


@pytest.mark.parametrize("model_name", [None, "", "   "])
def test_a_response_without_model_name_is_rejected(model_name: str | None) -> None:
    with pytest.raises(ExtractionRejectedError):
        reading_from(config(), PROMPT, model_name)


def test_the_instructions_are_the_prompt_text() -> None:
    seen: list[str | None] = []

    def spy(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info.instructions)
        return answer({"brand": "Drops", "grams": 50})

    extract(agent_on(FunctionModel(spy), Sample, retries=0), config(), PROMPT, "Drops, 50 g")

    assert seen == [PROMPT.text]


def test_an_absent_temperature_is_not_sent() -> None:
    sent: list[dict[str, object]] = []

    def spy(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        sent.append(dict(info.model_settings or {}))
        return answer({"brand": "Drops", "grams": 50})

    extract(agent_on(FunctionModel(spy), Sample, retries=0), config(), PROMPT, "Drops, 50 g")

    assert "temperature" not in sent[0]


def test_a_present_temperature_is_sent() -> None:
    sent: list[dict[str, object]] = []

    def spy(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        sent.append(dict(info.model_settings or {}))
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(spy), Sample, retries=0)
    extract(agent, config(temperature=0.2), PROMPT, "Drops, 50 g")

    assert sent[0]["temperature"] == pytest.approx(0.2)


def test_the_reading_is_set_by_the_code() -> None:
    def lies(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer(
            {
                "brand": "Drops",
                "grams": 50,
                "extracted_by": {"provider": "autre", "model": "autre"},
            }
        )

    agent = agent_on(TestModel(), Sample, retries=0)
    extraction = extract(agent, config(provider="mistral"), PROMPT, "Drops, 50 g")

    reading = extraction.reading
    assert reading.provider == "mistral"
    assert reading.model == "modele-fige-1"
    assert reading.model_version == "test"
    assert reading.prompt_id == "sample-v1"
    assert reading.prompt_sha256 == hashlib.sha256(PROMPT.text.encode("utf-8")).hexdigest()
    assert PROMPT.sha256 == reading.prompt_sha256

    ignored = extract(agent_on(FunctionModel(lies), Sample, retries=0), config(), PROMPT, "x")
    assert ignored.reading.provider == "anthropic"
    assert ignored.reading.model == "modele-fige-1"


def test_the_version_is_the_model_name_without_surrounding_spaces() -> None:
    reading = reading_from(config(), PROMPT, "  modele-1  ")

    assert reading.model_version == "modele-1"


@pytest.mark.parametrize(
    ("provider", "base_url"),
    [("anthropic", "https://a.test/v1/"), ("mistral", "https://m.test")],
)
def test_agent_for_gives_the_base_url_to_the_model(provider: Provider, base_url: str) -> None:
    agent = agent_for(config(provider=provider, base_url=base_url), Sample)

    assert agent.model is not None
    assert not isinstance(agent.model, str)
    assert agent.model.base_url == base_url


@pytest.mark.parametrize("retries", [0, 1])
def test_agent_for_applies_the_configured_retries(retries: int) -> None:
    calls: list[int] = []

    def always_off(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        return answer({"brand": "Drops", "grams": "pas un nombre"})

    settings = config(retries=retries)
    agent = agent_for(settings, Sample)

    with agent.override(model=FunctionModel(always_off)), pytest.raises(ExtractionRejectedError):
        extract(agent, settings, PROMPT, "Drops, 50 g")

    assert len(calls) == retries + 1


def test_agent_for_openai_uses_the_responses_model() -> None:
    agent = agent_for(config(provider="openai"), Sample)

    assert isinstance(agent.model, OpenAIResponsesModel)


def test_agent_for_moonshotai_reads_the_international_address_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MOONSHOTAI_BASE_URL", "http://piege.test/v1")

    agent = agent_for(config(provider="moonshotai"), Sample)

    assert isinstance(agent.model, OpenAIChatModel)
    assert agent.model.system == "moonshotai"
    assert agent.model.base_url == "https://api.moonshot.ai/v1/"


def test_agent_for_moonshotai_uses_the_configured_address() -> None:
    agent = agent_for(config(provider="moonshotai", base_url="https://api.moonshot.cn/v1"), Sample)

    assert agent.model is not None
    assert not isinstance(agent.model, str)
    assert agent.model.base_url == "https://api.moonshot.cn/v1/"


def test_agent_for_ollama_uses_the_local_address_without_a_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://piege.test/v1")
    monkeypatch.setenv("OLLAMA_API_KEY", "cle-de-l-environnement")

    agent = agent_for(config(provider="ollama"), Sample)

    assert isinstance(agent.model, OllamaModel)
    assert agent.model.base_url == f"{LOCAL_URL}/"
    assert agent.model.client.api_key == "ollama"


def test_agent_for_openrouter_fixes_the_host_without_fallback() -> None:
    agent = agent_for(config(provider="openrouter", host="mistral"), Sample)

    assert isinstance(agent.model, OpenRouterModel)
    settings = dict(agent.model.settings or {})
    assert settings["openrouter_provider"] == {
        "only": ["mistral"],
        "allow_fallbacks": False,
    }


def test_the_reading_keeps_the_host_returned_by_openrouter() -> None:
    reading = reading_from(
        config(provider="openrouter", host="mistral"), PROMPT, "nom-rendu", downstream="Mistral"
    )

    assert reading.host == "Mistral"


@pytest.mark.parametrize("downstream", [None, "", "  "])
def test_a_response_of_openrouter_without_host_is_rejected(downstream: str | None) -> None:
    with pytest.raises(ExtractionRejectedError):
        reading_from(
            config(provider="openrouter", host="mistral"),
            PROMPT,
            "nom-rendu",
            downstream=downstream,
        )


def test_the_other_providers_keep_no_host() -> None:
    reading = reading_from(config(), PROMPT, "nom-rendu", downstream="Ignore")

    assert reading.host is None


def test_extract_notes_the_host_returned_by_openrouter() -> None:
    def hosted(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(
            parts=[ToolCallPart("final_result", {"brand": "Drops", "grams": 50})],
            provider_details={"downstream_provider": "Mistral"},
        )

    agent = agent_on(FunctionModel(hosted), Sample, retries=0)
    settings = config(provider="openrouter", host="mistral")

    extraction = extract(agent, settings, PROMPT, "Drops, 50 g")

    assert extraction.reading.host == "Mistral"


def test_extract_rejects_an_openrouter_response_without_host() -> None:
    def unhosted(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(unhosted), Sample, retries=0)
    settings = config(provider="openrouter", host="mistral")

    with pytest.raises(ExtractionRejectedError):
        extract(agent, settings, PROMPT, "Drops, 50 g")


@pytest.mark.parametrize(
    "provider", ["anthropic", "mistral", "openai", "openrouter", "moonshotai", "ollama"]
)
def test_an_agent_for_a_provider_never_reaches_the_network(provider: Provider) -> None:
    settings = config(provider=provider, host="mistral")
    agent = agent_for(settings, Sample)

    with pytest.raises(RuntimeError, match="Model requests are not allowed"):
        extract(agent, settings, PROMPT, "Drops, 50 g")
