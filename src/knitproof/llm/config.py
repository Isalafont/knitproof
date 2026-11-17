"""La configuration d’un fournisseur, lue dans l’environnement (CLA-127, CLA-62, ADR 0033).

Fournisseurs : Anthropic, Mistral, OpenAI, OpenRouter (dont l’hébergeur est fixé), Kimi en direct
(Moonshot AI) et Ollama (modèle local, sans clé).

Aucune valeur par défaut cachée : un identifiant de modèle, une clé, un nombre de relances, un
nombre de réessais et une attente sur erreur passagère absents sont une erreur nommée. Un modèle
et un hébergeur donnés à `load_config` (CLA-199) remplacent `KNITPROOF_<P>_MODEL` et
`KNITPROOF_OPENROUTER_HOST`, avec les mêmes contrôles ; l’hébergeur n’existe que pour OpenRouter.
La température est facultative (ADR 0033) : `KNITPROOF_<P>_TEMPERATURE` prime sur
`KNITPROOF_LLM_TEMPERATURE`, et `omit` n’en envoie aucune.
"""

import math
from collections.abc import Mapping
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, SecretStr

from knitproof.llm.errors import InvalidSettingError, MissingSettingError

Provider = Literal["anthropic", "mistral", "openai", "openrouter", "moonshotai", "ollama"]

_KEYS: Mapping[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "moonshotai": "MOONSHOTAI_API_KEY",
}
_TEMPERATURE = "KNITPROOF_LLM_TEMPERATURE"
_RETRIES = "KNITPROOF_LLM_RETRIES"
_HTTP_RETRIES = "KNITPROOF_LLM_HTTP_RETRIES"
_HTTP_WAIT = "KNITPROOF_LLM_HTTP_WAIT"
MAX_WAIT_S = 60.0
_OMIT = "omit"


class ModelConfig(BaseModel):
    """Le fournisseur, l’identifiant figé du modèle et les réglages de l’appel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Provider
    model: str
    api_key: SecretStr | None
    base_url: str | None
    host: str | None
    temperature: float | None
    retries: int
    http_retries: int
    http_wait_s: float


def load_config(
    provider: Provider,
    environ: Mapping[str, str],
    *,
    model: str | None = None,
    host: str | None = None,
) -> ModelConfig:
    """Lit la configuration de `provider` dans `environ` (jamais `os.environ` d’office).

    `model` et `host`, quand ils sont donnés, remplacent les variables de l’environnement.
    """
    if provider not in get_args(Provider):
        raise InvalidSettingError("provider", f"{provider!r} inconnu")
    if host is not None and provider != "openrouter":
        raise InvalidSettingError("host", "un hébergeur n’existe que pour OpenRouter")
    prefix = f"KNITPROOF_{provider.upper()}"
    base_url = environ.get(f"{prefix}_BASE_URL") or None
    if provider == "ollama" and not base_url:
        raise MissingSettingError(f"{prefix}_BASE_URL")
    if provider == "openrouter" and base_url:
        raise InvalidSettingError(f"{prefix}_BASE_URL", "OpenRouter n’admet pas d’adresse propre")
    return ModelConfig(
        provider=provider,
        model=_model(environ, f"{prefix}_MODEL", model, local=provider == "ollama"),
        api_key=SecretStr(_required(environ, _KEYS[provider])) if provider in _KEYS else None,
        base_url=base_url,
        host=_host(environ, f"{prefix}_HOST", host) if provider == "openrouter" else None,
        temperature=_temperature(environ, prefix),
        retries=_retries(environ),
        http_retries=_count(environ, _HTTP_RETRIES),
        http_wait_s=_wait(environ),
    )


def _required(environ: Mapping[str, str], variable: str) -> str:
    value = environ.get(variable, "")
    if not value.strip():
        raise MissingSettingError(variable)
    return value


def _given_or_required(
    environ: Mapping[str, str], variable: str, given: str | None, field: str
) -> str:
    if given is None:
        return _required(environ, variable).strip()
    if not given.strip():
        raise MissingSettingError(field)
    return given.strip()


def _host(environ: Mapping[str, str], variable: str, given: str | None) -> str:
    return _given_or_required(environ, variable, given, "host")


def _model(environ: Mapping[str, str], variable: str, given: str | None, *, local: bool) -> str:
    model = _given_or_required(environ, variable, given, "model")
    if given is not None:
        variable = "model"
    if local and (":" not in model or model.lower().endswith(":latest")):
        raise InvalidSettingError(variable, "une étiquette explicite est attendue, pas « :latest »")
    if model.lower().endswith("-latest"):
        raise InvalidSettingError(variable, "un identifiant figé est attendu, pas « -latest »")
    return model


def _temperature(environ: Mapping[str, str], prefix: str) -> float | None:
    """La variable du fournisseur prime, même vide ; `omit` n’envoie aucune température."""
    variable = f"{prefix}_TEMPERATURE"
    if variable not in environ:
        variable = _TEMPERATURE
    text = environ.get(variable, "").strip()
    if not text or text.lower() == _OMIT:
        return None
    try:
        value = float(text)
    except ValueError:
        raise InvalidSettingError(variable, "un nombre entre 0 et 1 est attendu") from None
    if math.isnan(value) or not 0 <= value <= 1:
        raise InvalidSettingError(variable, "un nombre entre 0 et 1 est attendu")
    return value


def _retries(environ: Mapping[str, str]) -> int:
    return _count(environ, _RETRIES)


def _count(environ: Mapping[str, str], variable: str) -> int:
    text = _required(environ, variable).strip()
    if not (text.isascii() and text.isdigit()):
        raise InvalidSettingError(variable, "un entier positif ou nul est attendu")
    return int(text)


def _wait(environ: Mapping[str, str]) -> float:
    text = _required(environ, _HTTP_WAIT).strip()
    message = f"un nombre de secondes entre 0 et {MAX_WAIT_S:.0f} est attendu"
    try:
        value = float(text)
    except ValueError:
        raise InvalidSettingError(_HTTP_WAIT, message) from None
    if math.isnan(value) or not 0 <= value <= MAX_WAIT_S:
        raise InvalidSettingError(_HTTP_WAIT, message)
    return value
