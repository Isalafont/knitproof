"""La trace d’une lecture par un modèle (CLA-127, architecture §6, ADR 0033)."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmpty = Annotated[str, StringConstraints(min_length=1)]


class ModelReading(BaseModel):
    """Quel modèle a lu une source, avec quel prompt ; posée par le code, jamais par le modèle.

    `host` : hébergeur effectif derrière un agrégateur.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: NonEmpty
    model: NonEmpty
    model_version: NonEmpty
    prompt_id: NonEmpty
    prompt_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    host: NonEmpty | None = None
