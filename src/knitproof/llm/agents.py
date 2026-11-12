"""La fabrique d’agents pydanticAI, un par fournisseur (CLA-127, ADR 0033)."""

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.mistral import MistralProvider

from knitproof.llm.config import ModelConfig


def agent_on[C, T: BaseModel](
    model: Model[C], output_type: type[T], retries: int
) -> Agent[None, T]:
    """Un agent à sortie typée sur `model` ; `retries` ne borne que les relances de sortie."""
    return Agent(model, output_type=output_type, retries={"output": retries})


def agent_for[T: BaseModel](config: ModelConfig, output_type: type[T]) -> Agent[None, T]:
    """L’agent du fournisseur de `config`, construit sans appel réseau."""
    key = config.api_key.get_secret_value()
    if config.provider == "anthropic":
        anthropic = AnthropicModel(
            config.model, provider=AnthropicProvider(api_key=key, base_url=config.base_url)
        )
        return agent_on(anthropic, output_type, config.retries)
    mistral = MistralModel(
        config.model, provider=MistralProvider(api_key=key, base_url=config.base_url)
    )
    return agent_on(mistral, output_type, config.retries)
