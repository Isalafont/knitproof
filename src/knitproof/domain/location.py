"""Où se trouve un élément dans le document source."""

from typing import Self

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator


class SourceLocation(BaseModel):
    """Page et ligne d’un élément du patron, au moins l’une des deux."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    page: PositiveInt | None = None
    line: PositiveInt | None = None

    @model_validator(mode="after")
    def _has_a_position(self) -> Self:
        if self.page is None and self.line is None:
            raise ValueError("une localisation porte au moins une page ou une ligne")
        return self
