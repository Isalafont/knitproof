"""Âge de la spécification, saisi en mois puis en années (CLA-112, ADR 0018 §8)."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from knitproof.domain.integers import StrictNonNegativeInt

MONTHS_PER_YEAR = 12
MONTHS_BEFORE_YEARS = 24
YEARS_FROM = MONTHS_BEFORE_YEARS // MONTHS_PER_YEAR


class AgeUnit(StrEnum):
    MONTHS = "months"
    YEARS = "years"


class Age(BaseModel):
    """Un âge, avec son unité d’origine : en mois avant 2 ans, en années ensuite.

    Un âge en années vaut le mois exact : 3 ans = 36 mois, sans enveloppe (ADR 0018 §8).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: StrictNonNegativeInt
    unit: AgeUnit

    @model_validator(mode="after")
    def _unit_fits_the_value(self) -> Self:
        if self.unit is AgeUnit.YEARS and self.value < YEARS_FROM:
            raise ValueError("l’âge se saisit en mois avant 2 ans")
        if self.unit is AgeUnit.MONTHS and self.value >= MONTHS_BEFORE_YEARS:
            raise ValueError("l’âge se saisit en années à partir de 2 ans")
        return self

    @property
    def in_months(self) -> int:
        if self.unit is AgeUnit.YEARS:
            return self.value * MONTHS_PER_YEAR
        return self.value
