"""L’appel de sortie structurée : la valeur validée et sa trace, posée par le code (CLA-127).

Le modèle ne produit que la valeur ; `reading` (fournisseur, modèle, version, prompt) vient de
`config`, du `Prompt` et de la réponse, jamais de la sortie du modèle (architecture §7).
"""

import hashlib
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.settings import ModelSettings

from knitproof.domain.reading import ModelReading
from knitproof.llm.config import ModelConfig
from knitproof.llm.errors import ExtractionRejectedError


@dataclass(frozen=True)
class Prompt:
    """Un prompt versionné : son identifiant et son texte ; l’empreinte en est tirée."""

    id: str
    text: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


class TokenUsage(BaseModel):
    """Les jetons d’un appel ; `None` quand le fournisseur ne les a pas mesurés (jamais 0)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_tokens: int | None
    output_tokens: int | None


class Extraction[T: BaseModel](BaseModel):
    """Une valeur validée par son schéma, avec la trace de la lecture."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    value: T
    reading: ModelReading
    usage: TokenUsage


def extract[T: BaseModel](
    agent: Agent[None, T], config: ModelConfig, prompt: Prompt, source: str
) -> Extraction[T]:
    """Lance l’appel ; une sortie hors schéma après les relances lève `ExtractionRejectedError`."""
    settings = (
        ModelSettings(temperature=config.temperature) if config.temperature is not None else None
    )
    try:
        result = agent.run_sync(source, instructions=prompt.text, model_settings=settings)
    except UnexpectedModelBehavior as error:
        raise ExtractionRejectedError(f"sortie du modèle refusée : {error}") from error
    downstream = (result.response.provider_details or {}).get("downstream_provider")
    reading = reading_from(config, prompt, result.response.model_name, downstream)
    usage = result.usage  # propriété : `usage()` est dépréciée
    measured = usage.unmeasured_requests == 0
    tokens = TokenUsage(
        input_tokens=usage.input_tokens if measured else None,
        output_tokens=usage.output_tokens if measured else None,
    )
    return Extraction(value=result.output, reading=reading, usage=tokens)


def reading_from(
    config: ModelConfig, prompt: Prompt, model_name: str | None, downstream: str | None = None
) -> ModelReading:
    """La trace d’une lecture ; sans nom de modèle rendu par la réponse, elle est refusée.

    Pour OpenRouter, `downstream` est l’hébergeur effectif rendu par la réponse ; sans lui, la
    trace est refusée. Les autres fournisseurs n’ont pas d’hébergeur.
    """
    version = (model_name or "").strip()
    if not version:
        raise ExtractionRejectedError("la réponse ne donne pas le nom du modèle")
    host: str | None = None
    if config.provider == "openrouter":
        host = (downstream or "").strip()
        if not host:
            raise ExtractionRejectedError("la réponse ne donne pas l’hébergeur du modèle")
    return ModelReading(
        provider=config.provider,
        model=config.model,
        model_version=version,
        host=host,
        prompt_id=prompt.id,
        prompt_sha256=prompt.sha256,
    )
