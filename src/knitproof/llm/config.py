"""La configuration d’un fournisseur, lue dans l’environnement (CLA-127, ADR 0033).

Aucune valeur par défaut cachée : un identifiant de modèle, une clé et un nombre de relances
absents sont une erreur nommée. La température est facultative (ADR 0033).
"""

import math
from collections.abc import Mapping
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, SecretStr

from knitproof.llm.errors import InvalidSettingError, MissingSettingError

Provider = Literal["anthropic", "mistral"]

_KEYS: Mapping[Provider, str] = {"anthropic": "ANTHROPIC_API_KEY", "mistral": "MISTRAL_API_KEY"}
_TEMPERATURE = "KNITPROOF_LLM_TEMPERATURE"
_RETRIES = "KNITPROOF_LLM_RETRIES"


class ModelConfig(BaseModel):
    """Le fournisseur, l’identifiant figé du modèle et les réglages de l’appel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Provider
    model: str
    api_key: SecretStr
    base_url: str | None
    temperature: float | None
    retries: int


def load_config(provider: Provider, environ: Mapping[str, str]) -> ModelConfig:
    """Lit la configuration de `provider` dans `environ` (jamais `os.environ` d’office)."""
    if provider not in get_args(Provider):
        raise InvalidSettingError("provider", f"{provider!r} inconnu")
    prefix = f"KNITPROOF_{provider.upper()}"
    return ModelConfig(
        provider=provider,
        model=_model(environ, f"{prefix}_MODEL"),
        api_key=SecretStr(_required(environ, _KEYS[provider])),
        base_url=environ.get(f"{prefix}_BASE_URL") or None,
        temperature=_temperature(environ),
        retries=_retries(environ),
    )


def _required(environ: Mapping[str, str], variable: str) -> str:
    value = environ.get(variable, "")
    if not value.strip():
        raise MissingSettingError(variable)
    return value


def _model(environ: Mapping[str, str], variable: str) -> str:
    model = _required(environ, variable).strip()
    if model.lower().endswith("-latest"):
        raise InvalidSettingError(variable, "un identifiant figé est attendu, pas « -latest »")
    return model


def _temperature(environ: Mapping[str, str]) -> float | None:
    text = environ.get(_TEMPERATURE, "").strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        raise InvalidSettingError(_TEMPERATURE, "un nombre entre 0 et 1 est attendu") from None
    if math.isnan(value) or not 0 <= value <= 1:
        raise InvalidSettingError(_TEMPERATURE, "un nombre entre 0 et 1 est attendu")
    return value


def _retries(environ: Mapping[str, str]) -> int:
    text = _required(environ, _RETRIES).strip()
    if not (text.isascii() and text.isdigit()):
        raise InvalidSettingError(_RETRIES, "un entier positif ou nul est attendu")
    return int(text)
