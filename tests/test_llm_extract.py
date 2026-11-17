"""L’appel de sortie structurée et sa trace (CLA-127, ADR 0033)."""

import hashlib
import itertools
from collections.abc import Callable, Sequence

import httpx2 as httpx
import pytest
from pydantic import BaseModel, SecretStr
from pydantic_ai import Agent, models
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.providers.moonshotai import MoonshotAIProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.usage import RequestUsage

from knitproof.llm.agents import agent_for, agent_on
from knitproof.llm.config import ModelConfig, Provider
from knitproof.llm.errors import ExtractionRejectedError, TransientCallError
from knitproof.llm.extract import Extraction, Prompt, extract, reading_from

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
    http_retries: int = 0,
    http_wait_s: float = 0.0,
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
        http_retries=http_retries,
        http_wait_s=http_wait_s,
    )


def call[T: BaseModel](
    agent: Agent[None, T],
    config: ModelConfig,
    prompt: Prompt,
    source: str,
    *,
    clock: Callable[[], float] = lambda: 0.0,
    sleep: Callable[[float], None] = lambda seconds: None,
) -> Extraction[T]:
    return extract(agent, config, prompt, source, clock=clock, sleep=sleep)


def answer(arguments: dict[str, object]) -> ModelResponse:
    return ModelResponse(parts=[ToolCallPart("final_result", arguments)])


def test_real_requests_are_blocked() -> None:
    model = AnthropicModel("claude-sonnet-4-5", provider=AnthropicProvider(api_key="fake"))
    agent = Agent(model)
    with pytest.raises(RuntimeError, match="Model requests are not allowed"):
        agent.run_sync("bonjour")


def test_a_test_model_returns_a_validated_object() -> None:
    agent = agent_on(TestModel(), Sample, retries=0)

    extraction = call(agent, config(), PROMPT, "Drops, 50 g")

    assert isinstance(extraction.value, Sample)


def test_an_output_off_schema_is_rejected() -> None:
    def off_schema(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer({"brand": "Drops", "grams": "pas un nombre"})

    agent = agent_on(FunctionModel(off_schema), Sample, retries=0)

    with pytest.raises(ExtractionRejectedError):
        call(agent, config(), PROMPT, "Drops, 50 g")


def test_one_output_retry_is_allowed() -> None:
    calls: list[int] = []

    def fails_once(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        if len(calls) == 1:
            return answer({"brand": "Drops", "grams": "pas un nombre"})
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(fails_once), Sample, retries=1)

    extraction = call(agent, config(retries=1), PROMPT, "Drops, 50 g")

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
        call(agent, config(retries=retries), PROMPT, "Drops, 50 g")

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

    call(agent_on(FunctionModel(spy), Sample, retries=0), config(), PROMPT, "Drops, 50 g")

    assert seen == [PROMPT.text]


def test_an_absent_temperature_is_not_sent() -> None:
    sent: list[dict[str, object]] = []

    def spy(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        sent.append(dict(info.model_settings or {}))
        return answer({"brand": "Drops", "grams": 50})

    call(agent_on(FunctionModel(spy), Sample, retries=0), config(), PROMPT, "Drops, 50 g")

    assert "temperature" not in sent[0]


def test_a_present_temperature_is_sent() -> None:
    sent: list[dict[str, object]] = []

    def spy(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        sent.append(dict(info.model_settings or {}))
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(spy), Sample, retries=0)
    call(agent, config(temperature=0.2), PROMPT, "Drops, 50 g")

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
    extraction = call(agent, config(provider="mistral"), PROMPT, "Drops, 50 g")

    reading = extraction.reading
    assert reading.provider == "mistral"
    assert reading.model == "modele-fige-1"
    assert reading.model_version == "test"
    assert reading.prompt_id == "sample-v1"
    assert reading.prompt_sha256 == hashlib.sha256(PROMPT.text.encode("utf-8")).hexdigest()
    assert PROMPT.sha256 == reading.prompt_sha256

    ignored = call(agent_on(FunctionModel(lies), Sample, retries=0), config(), PROMPT, "x")
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
        call(agent, settings, PROMPT, "Drops, 50 g")

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

    extraction = call(agent, settings, PROMPT, "Drops, 50 g")

    assert extraction.reading.host == "Mistral"


def test_extract_rejects_an_openrouter_response_without_host() -> None:
    def unhosted(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(unhosted), Sample, retries=0)
    settings = config(provider="openrouter", host="mistral")

    with pytest.raises(ExtractionRejectedError):
        call(agent, settings, PROMPT, "Drops, 50 g")


@pytest.mark.parametrize(
    "provider", ["anthropic", "mistral", "openai", "openrouter", "moonshotai", "ollama"]
)
def test_an_agent_for_a_provider_never_reaches_the_network(provider: Provider) -> None:
    settings = config(provider=provider, host="mistral")
    agent = agent_for(settings, Sample)

    with pytest.raises(RuntimeError, match="Model requests are not allowed"):
        call(agent, settings, PROMPT, "Drops, 50 g")


def test_the_tokens_of_a_call_are_returned() -> None:
    def counted(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(
            parts=[ToolCallPart("final_result", {"brand": "Drops", "grams": 50})],
            usage=RequestUsage(input_tokens=51, output_tokens=4),
        )

    agent = agent_on(FunctionModel(counted), Sample, retries=0)

    extraction = call(agent, config(), PROMPT, "Drops, 50 g")

    assert extraction.usage.input_tokens == 51
    assert extraction.usage.output_tokens == 4


def test_unmeasured_tokens_are_unknown_not_zero() -> None:
    def unmeasured(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(
            parts=[ToolCallPart("final_result", {"brand": "Drops", "grams": 50})],
            usage=RequestUsage(unmeasured_requests=1),
        )

    agent = agent_on(FunctionModel(unmeasured), Sample, retries=0)

    extraction = call(agent, config(), PROMPT, "Drops, 50 g")

    assert extraction.usage.input_tokens is None
    assert extraction.usage.output_tokens is None


def _spy_settings() -> tuple[
    list[dict[str, object]], Callable[[Sequence[ModelMessage], AgentInfo], ModelResponse]
]:
    sent: list[dict[str, object]] = []

    def spy(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        sent.append(dict(info.model_settings or {}))
        return answer({"brand": "Drops", "grams": 50})

    return sent, spy


@pytest.mark.parametrize("temperature", [None, 0.0])
def test_the_sdk_retries_are_always_switched_off(temperature: float | None) -> None:
    sent, spy = _spy_settings()

    call(
        agent_on(FunctionModel(spy), Sample, retries=0),
        config(temperature=temperature),
        PROMPT,
        "x",
    )

    assert sent[0]["max_retries"] == 0
    assert ("temperature" in sent[0]) is (temperature is not None)


class Failing:
    """Un modèle qui lève les erreurs données une à une, puis répond."""

    def __init__(self, *errors: Exception) -> None:
        self.errors = list(errors)
        self.calls = 0

    def __call__(self, messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return answer({"brand": "Drops", "grams": 50})


def http(status: int, retry_after: str | None = None) -> ModelHTTPError:
    headers = {"retry-after": retry_after} if retry_after else None
    return ModelHTTPError(status, "modele", body=None, headers=headers)


def retrying(
    model: Failing, *, retries: int = 3, wait: float = 1.0, clock: Callable[[], float] | None = None
) -> tuple[Extraction[Sample], list[float]]:
    waits: list[float] = []
    agent = agent_on(FunctionModel(model), Sample, retries=0)
    cfg = config(http_retries=retries, http_wait_s=wait)
    extraction = call(agent, cfg, PROMPT, "x", clock=clock or (lambda: 0.0), sleep=waits.append)
    return extraction, waits


def test_a_429_is_retried_after_the_base_wait() -> None:
    model = Failing(http(429))

    extraction, waits = retrying(model, wait=2.0)

    assert extraction.attempts == 2
    assert waits == [2.0]


@pytest.mark.parametrize("status", [429, 500, 502, 503, 529])
def test_a_429_or_a_5xx_is_retried(status: int) -> None:
    model = Failing(http(status))

    extraction, _ = retrying(model)

    assert extraction.attempts == 2
    assert model.calls == 2


@pytest.mark.parametrize("status", [400, 401, 404])
def test_another_status_is_not_retried(status: int) -> None:
    model = Failing(http(status))

    with pytest.raises(ModelHTTPError):
        retrying(model)

    assert model.calls == 1


def test_an_api_error_without_status_is_not_retried() -> None:
    model = Failing(ModelAPIError("modele", "coupure"))

    with pytest.raises(ModelAPIError):
        retrying(model)

    assert model.calls == 1


def test_no_http_retry_means_one_call() -> None:
    model = Failing(http(429))

    with pytest.raises(TransientCallError):
        retrying(model, retries=0)

    assert model.calls == 1


def test_an_endless_429_stops_after_the_budget_with_a_doubling_wait() -> None:
    model = Failing(*[http(429) for _ in range(10)])
    waits: list[float] = []
    agent = agent_on(FunctionModel(model), Sample, retries=0)

    with pytest.raises(TransientCallError) as raised:
        call(agent, config(http_retries=3, http_wait_s=1.5), PROMPT, "x", sleep=waits.append)

    assert model.calls == 4
    assert waits == [1.5, 3.0, 6.0]
    assert raised.value.attempts == 4
    assert isinstance(raised.value.__cause__, ModelHTTPError)


@pytest.mark.parametrize(("retry_after", "expected"), [("7", 7.0), ("300", 60.0), ("0", 1.0)])
def test_the_wait_follows_retry_after_up_to_the_cap(retry_after: str, expected: float) -> None:
    model = Failing(http(429, retry_after))

    _, waits = retrying(model, wait=1.0)

    assert waits == [expected]


def test_the_wait_is_capped_even_without_retry_after() -> None:
    model = Failing(http(503), http(503))

    _, waits = retrying(model, wait=40.0)

    assert waits == [40.0, 60.0]


def test_the_latency_counts_only_the_attempt_that_answers() -> None:
    model = Failing(http(429), http(429))
    ticks = iter([0.0, 10.0, 20.0, 20.5])  # trois débuts d’essai, puis la fin du dernier

    extraction, _ = retrying(model, clock=lambda: next(ticks))

    assert extraction.attempts == 3
    assert extraction.latency_ms == 500


def test_a_rejected_output_after_a_429_keeps_the_attempts() -> None:
    errors: list[Exception] = [http(429)]

    def off_schema(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        if errors:
            raise errors.pop()
        return answer({"brand": "Drops", "grams": "pas un nombre"})

    agent = agent_on(FunctionModel(off_schema), Sample, retries=0)

    with pytest.raises(ExtractionRejectedError) as raised:
        call(agent, config(http_retries=2), PROMPT, "x")

    assert raised.value.attempts == 2


def test_an_openrouter_reading_without_host_after_a_429_keeps_attempts_and_latency() -> None:
    errors: list[Exception] = [http(429)]

    def without_host(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        if errors:
            raise errors.pop()
        return answer({"brand": "Drops", "grams": 50})

    agent = agent_on(FunctionModel(without_host), Sample, retries=0)
    ticks = itertools.count()

    with pytest.raises(ExtractionRejectedError) as raised:
        call(
            agent,
            config(provider="openrouter", host="vendeur", http_retries=2),
            PROMPT,
            "x",
            clock=lambda: next(ticks) * 0.25,
        )

    assert raised.value.attempts == 2
    assert raised.value.latency_ms == 250


def _agent_on_client(provider: Provider, client: httpx.AsyncClient) -> Agent[None, Sample]:
    match provider:
        case "anthropic":
            anthropic = AnthropicModel(
                "m", provider=AnthropicProvider(api_key="k", http_client=client)
            )
            return agent_on(anthropic, Sample, retries=0)
        case "mistral":
            mistral = MistralModel("m", provider=MistralProvider(api_key="k", http_client=client))
            return agent_on(mistral, Sample, retries=0)
        case "openai":
            openai = OpenAIResponsesModel(
                "m", provider=OpenAIProvider(api_key="k", http_client=client)
            )
            return agent_on(openai, Sample, retries=0)
        case "openrouter":
            router = OpenRouterModel(
                "vendeur/m", provider=OpenRouterProvider(api_key="k", http_client=client)
            )
            return agent_on(router, Sample, retries=0)
        case "moonshotai":
            kimi = OpenAIChatModel(
                "m",
                provider=MoonshotAIProvider(
                    api_key="k", base_url="https://api.moonshot.ai/v1", http_client=client
                ),
            )
            return agent_on(kimi, Sample, retries=0)
        case "ollama":
            local = OllamaModel(
                "m:8b",
                provider=OllamaProvider(base_url=LOCAL_URL, api_key="ollama", http_client=client),
            )
            return agent_on(local, Sample, retries=0)


@pytest.mark.parametrize(
    "provider", ["anthropic", "mistral", "openai", "openrouter", "moonshotai", "ollama"]
)
def test_a_provider_receives_a_single_request_when_retries_are_off(
    provider: Provider, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Garde-fou : une montée de pydanticAI qui ignorerait `max_retries` ferait échouer ce test."""
    monkeypatch.setattr(models, "ALLOW_MODEL_REQUESTS", True)
    seen: list[httpx.Request] = []

    def refuse(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            429,
            headers={"retry-after-ms": "1", "retry-after": "0"},
            json={"error": {"message": "limite", "code": 429}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(refuse))
    agent = _agent_on_client(provider, client)

    with pytest.raises(TransientCallError):
        call(agent, config(provider=provider), PROMPT, "x")

    assert len(seen) == 1
