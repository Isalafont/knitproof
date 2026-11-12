import pytest
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider


def test_real_requests_are_blocked() -> None:
    model = AnthropicModel("claude-sonnet-4-5", provider=AnthropicProvider(api_key="fake"))
    agent = Agent(model)
    with pytest.raises(RuntimeError, match="Model requests are not allowed"):
        agent.run_sync("bonjour")
