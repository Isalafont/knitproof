"""L’appel de sortie structurée : la valeur validée et sa trace, posée par le code (CLA-127).

Le modèle ne produit que la valeur ; `reading` (fournisseur, modèle, version, prompt) vient de
`config`, du `Prompt` et de la réponse, jamais de la sortie du modèle (architecture §7).
"""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.settings import ModelSettings

from knitproof.domain.reading import ModelReading
from knitproof.llm.config import MAX_WAIT_S, ModelConfig
from knitproof.llm.errors import ExtractionRejectedError, TransientCallError

_TOO_MANY_REQUESTS = 429
_FIRST_5XX = 500
_LAST_5XX = 599
_MS = 1000


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
    attempts: int
    latency_ms: int


def is_transient(error: ModelHTTPError) -> bool:
    """429 et 5xx : une erreur passagère, qui vaut un réessai. Le tri se fait sur le statut."""
    return error.status_code == _TOO_MANY_REQUESTS or _FIRST_5XX <= error.status_code <= _LAST_5XX


def extract[T: BaseModel](
    agent: Agent[None, T],
    config: ModelConfig,
    prompt: Prompt,
    source: str,
    *,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
) -> Extraction[T]:
    """Lance l’appel, réessayé sur 429 ou 5xx ; une sortie hors schéma est refusée.

    Les réessais des SDK sont coupés (`max_retries=0`) : seule cette boucle réessaie, au plus
    `config.http_retries` fois, avec une attente doublée à chaque fois (`Retry-After` si plus
    long), plafonnée à `MAX_WAIT_S`. Les essais épuisés lèvent `TransientCallError`, une sortie
    refusée `ExtractionRejectedError`.
    """
    settings = ModelSettings(max_retries=0)
    if config.temperature is not None:
        settings["temperature"] = config.temperature
    attempts = 0
    while True:
        attempts += 1
        began = clock()
        try:
            result = agent.run_sync(source, instructions=prompt.text, model_settings=settings)
        except UnexpectedModelBehavior as error:
            raise ExtractionRejectedError(
                f"sortie du modèle refusée : {error}",
                attempts=attempts,
                latency_ms=_since(clock, began),
            ) from error
        except ModelHTTPError as error:
            if not is_transient(error):
                raise
            if attempts > config.http_retries:
                raise TransientCallError(
                    f"{config.provider} : erreur {error.status_code} après {attempts} essai(s)",
                    attempts=attempts,
                ) from error
            sleep(_wait(config, attempts, error))
            continue
        break
    latency_ms = _since(clock, began)
    downstream = (result.response.provider_details or {}).get("downstream_provider")
    try:
        reading = reading_from(config, prompt, result.response.model_name, downstream)
    except ExtractionRejectedError as error:
        raise ExtractionRejectedError(
            str(error), attempts=attempts, latency_ms=latency_ms
        ) from error
    usage = result.usage  # propriété : `usage()` est dépréciée
    measured = usage.unmeasured_requests == 0
    tokens = TokenUsage(
        input_tokens=usage.input_tokens if measured else None,
        output_tokens=usage.output_tokens if measured else None,
    )
    return Extraction(
        value=result.output, reading=reading, usage=tokens, attempts=attempts, latency_ms=latency_ms
    )


def _since(clock: Callable[[], float], began: float) -> int:
    return round((clock() - began) * _MS)


def _wait(config: ModelConfig, retry: int, error: ModelHTTPError) -> float:
    """L’attente avant le réessai `retry` : doublée à chaque fois, portée au `Retry-After`."""
    return min(max(config.http_wait_s * 2.0 ** (retry - 1), error.retry_after or 0.0), MAX_WAIT_S)


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
