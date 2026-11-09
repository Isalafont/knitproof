"""Question en attente : ce que le plan demande à la personne (CLA-68)."""

from pydantic import BaseModel, ConfigDict, Field


class PendingQuestion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1)
    text: str = Field(min_length=1, pattern=r"\S")
    options: tuple[str, ...]
