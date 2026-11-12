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


class Extraction[T: BaseModel](BaseModel):
    """Une valeur validée par son schéma, avec la trace de la lecture."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    value: T
    reading: ModelReading


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
    reading = reading_from(config, prompt, result.response.model_name)
    return Extraction(value=result.output, reading=reading)


def reading_from(config: ModelConfig, prompt: Prompt, model_name: str | None) -> ModelReading:
    """La trace d’une lecture ; sans nom de modèle rendu par la réponse, elle est refusée."""
    version = (model_name or "").strip()
    if not version:
        raise ExtractionRejectedError("la réponse ne donne pas le nom du modèle")
    return ModelReading(
        provider=config.provider,
        model=config.model,
        model_version=version,
        prompt_id=prompt.id,
        prompt_sha256=prompt.sha256,
    )
