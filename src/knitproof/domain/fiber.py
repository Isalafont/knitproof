"""Vocabulaire des fibres et composition d’un fil (CLA-121, ADR 0030).

Une fibre n’a ni chiffre ni avertissement : elle dit seulement quels noms la désignent.
"""

import unicodedata
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from knitproof.domain.measure import PlainDecimal
from knitproof.domain.provenance import SourcedEntry

TOTAL_PERCENT = 100

type Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def name_key(name: str) -> str:
    """La clé de comparaison d’un nom : NFC puis `casefold()` ; l’accent est gardé."""
    return unicodedata.normalize("NFC", name).casefold()


class Fiber(SourcedEntry):
    """Une fibre : un `id` et les noms qui la désignent (au moins un, uniques par clé)."""

    names: tuple[Name, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _names_are_unique(self) -> Self:
        keys = [name_key(name) for name in self.names]
        if len(set(keys)) != len(keys):
            raise ValueError("nom en double dans une fibre")
        return self


class FiberShare(BaseModel):
    """La part d’une fibre : son `id`, le terme de l’étiquette tel qu’écrit, son pourcentage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fiber: Annotated[str, StringConstraints(min_length=1)]
    label_term: Name
    percent: Annotated[PlainDecimal, Field(le=TOTAL_PERCENT)]


class FiberComposition(BaseModel):
    """Les parts d’un fil : une fibre au plus une fois, somme égale à 100."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parts: tuple[FiberShare, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _is_a_whole(self) -> Self:
        fibers = [part.fiber for part in self.parts]
        if len(set(fibers)) != len(fibers):
            raise ValueError("fibre en double dans la composition")
        if sum((part.percent for part in self.parts), Decimal(0)) != TOTAL_PERCENT:
            raise ValueError(f"somme != {TOTAL_PERCENT}")
        return self
