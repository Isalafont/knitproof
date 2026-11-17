"""Les entrées de `--models` : `fournisseur[:modèle][@hébergeur]` (CLA-199)."""

from typing import TypeGuard, get_args

from pydantic import BaseModel, ConfigDict

from knitproof.llm.config import Provider

PROVIDER_NAMES: tuple[str, ...] = get_args(Provider)


class ModelEntryError(Exception):
    """Une entrée mal formée ; le message la nomme telle que tapée."""


class ModelEntry(BaseModel):
    """Une entrée lue ; `None` : la valeur vient de `.env`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    provider: Provider
    model: str | None
    host: str | None


def parse_entry(text: str) -> ModelEntry:
    """Coupe au dernier `@` (hébergeur), puis au premier `:` (le reste est le modèle)."""
    head, at, host = text.rpartition("@")
    if not at:
        head, host = text, ""
    provider, colon, model = head.partition(":")
    if not _is_provider(provider):
        raise ModelEntryError(
            f"entrée « {text} » : fournisseur « {provider} » inconnu ; "
            f"attendus : {', '.join(PROVIDER_NAMES)}"
        )
    if colon and not model.strip():
        raise ModelEntryError(f"entrée « {text} » : modèle vide après « : »")
    if at and not host.strip():
        raise ModelEntryError(f"entrée « {text} » : hébergeur vide après « @ »")
    if at and provider != "openrouter":
        raise ModelEntryError(f"entrée « {text} » : « @ » n’existe que pour openrouter")
    return ModelEntry(
        text=text,
        provider=provider,
        model=model.strip() if colon else None,
        host=host.strip() if at else None,
    )


def _is_provider(name: str) -> TypeGuard[Provider]:
    return name in PROVIDER_NAMES
