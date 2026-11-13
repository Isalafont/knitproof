"""Appel de contrôle réel, un par fournisseur, lancé à la main (CLA-127, CA5).

Lancement : `uv run --env-file .env pytest -m live -k anthropic`, puis `-k mistral`.
"""

import os

import pytest
from pydantic import BaseModel
from pydantic_ai import models

from knitproof.llm.agents import agent_for
from knitproof.llm.config import Provider, load_config
from knitproof.llm.errors import LlmError
from knitproof.llm.extract import Prompt, extract

CONTROL = Prompt(id="control-v1", text="Rends la marque et le poids de ce texte.")


class ControlAnswer(BaseModel):
    brand: str
    grams: int


@pytest.mark.live
@pytest.mark.parametrize("provider", ["anthropic", "mistral", "openai"])
def test_a_real_call_returns_a_validated_object(
    provider: Provider, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(models, "ALLOW_MODEL_REQUESTS", True)
    try:
        config = load_config(provider, os.environ)
    except LlmError as error:
        pytest.fail(str(error), pytrace=False)

    extraction = extract(agent_for(config, ControlAnswer), config, CONTROL, "Drops Alpaca, 50 g")

    assert isinstance(extraction.value, ControlAnswer)
    assert extraction.reading.model_version
