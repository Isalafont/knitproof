"""Une entrée de `--models` se lit en fournisseur, modèle et hébergeur (CLA-199)."""

from typing import get_args

import pytest

from knitproof.app.model_entries import ModelEntry, ModelEntryError, parse_entry
from knitproof.llm.config import Provider


@pytest.mark.parametrize(
    ("text", "provider", "model", "host"),
    [
        ("anthropic", "anthropic", None, None),
        ("ollama:qwen3:8b", "ollama", "qwen3:8b", None),
        (
            "openrouter:mistralai/mistral-small-3.2-24b-instruct@mistral/eu",
            "openrouter",
            "mistralai/mistral-small-3.2-24b-instruct",
            "mistral/eu",
        ),
        (
            "openrouter:moonshotai/kimi-k3.1-pro@moonshotai",
            "openrouter",
            "moonshotai/kimi-k3.1-pro",
            "moonshotai",
        ),
        ("openrouter@mistral/eu", "openrouter", None, "mistral/eu"),
        ("openrouter:x:free", "openrouter", "x:free", None),
        ("openrouter:a@b@c", "openrouter", "a@b", "c"),
    ],
)
def test_an_entry_is_read_as_provider_model_and_host(
    text: str, provider: Provider, model: str | None, host: str | None
) -> None:
    assert parse_entry(text) == ModelEntry(text=text, provider=provider, model=model, host=host)


@pytest.mark.parametrize("text", ["ollama:", "openrouter:x@", "anthropic@x", "openrouter:@a"])
def test_a_malformed_entry_is_refused_and_named(text: str) -> None:
    with pytest.raises(ModelEntryError, match=text):
        parse_entry(text)


def test_an_unknown_provider_is_refused_with_the_known_ones() -> None:
    with pytest.raises(ModelEntryError, match="gemini:x") as info:
        parse_entry("gemini:x")

    assert all(name in str(info.value) for name in get_args(Provider))
