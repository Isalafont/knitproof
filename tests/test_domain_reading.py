"""La trace d’une lecture par un modèle (CLA-127, ADR 0033)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.reading import ModelReading

SHA = "a" * 64
FIELDS = {
    "provider": "anthropic",
    "model": "claude-sonnet-4-5",
    "model_version": "claude-sonnet-4-5-20250929",
    "prompt_id": "extract-yarn-label-v1",
    "prompt_sha256": SHA,
}


def test_a_reading_keeps_its_fields() -> None:
    reading = ModelReading.model_validate(FIELDS)

    assert reading.provider == "anthropic"
    assert reading.model == "claude-sonnet-4-5"
    assert reading.model_version == "claude-sonnet-4-5-20250929"
    assert reading.prompt_id == "extract-yarn-label-v1"
    assert reading.prompt_sha256 == SHA


@pytest.mark.parametrize("sha", ["", "A" * 64, "a" * 63, "a" * 65, "g" * 64])
def test_a_prompt_hash_must_be_64_lowercase_hexadecimals(sha: str) -> None:
    with pytest.raises(ValidationError, match="prompt_sha256"):
        ModelReading.model_validate({**FIELDS, "prompt_sha256": sha})


@pytest.mark.parametrize("field", ["provider", "model", "model_version", "prompt_id"])
def test_an_empty_field_is_refused(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        ModelReading.model_validate({**FIELDS, field: ""})


def test_an_extra_field_is_refused() -> None:
    with pytest.raises(ValidationError, match="extra"):
        ModelReading.model_validate({**FIELDS, "extra": "x"})


def test_a_reading_is_frozen() -> None:
    reading = ModelReading.model_validate(FIELDS)
    with pytest.raises(ValidationError, match="frozen"):
        reading.model = "autre"  # type: ignore[misc]


def test_a_reading_has_no_host_by_default() -> None:
    assert ModelReading.model_validate(FIELDS).host is None


def test_a_reading_keeps_the_host_behind_an_aggregator() -> None:
    reading = ModelReading.model_validate({**FIELDS, "host": "Mistral"})

    assert reading.host == "Mistral"


def test_an_empty_host_is_refused() -> None:
    with pytest.raises(ValidationError, match="host"):
        ModelReading.model_validate({**FIELDS, "host": ""})
