"""Mesures de référence : tour de tête par âge, hauteur par ligne (CLA-67, ADR 0020 et 0027).

Une mesure garde l’unité de sa source et n’a aucune valeur proposée : la source publie une
plage ou une valeur, pas un milieu.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from knitproof.domain.age import Age
from knitproof.domain.head_size import Sex
from knitproof.domain.integers import StrictNonNegativeInt
from knitproof.domain.measure import Length, LengthUnit, PlainDecimal
from knitproof.domain.provenance import SourcedEntry


class Quantity(StrEnum):
    HEAD_CIRCUMFERENCE = "head_circumference"
    HEIGHT = "height"


class AgeBounds(BaseModel):
    """Bornes d’âge incluses, en mois ; sans borne haute, tous les âges au-dessus."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_months: StrictNonNegativeInt
    max_months: StrictNonNegativeInt | None = None

    @model_validator(mode="after")
    def _upper_bound_is_not_below_the_lower(self) -> Self:
        if self.max_months is not None and self.max_months < self.min_months:
            raise ValueError("max_months ne peut pas être sous min_months")
        return self

    def contains(self, age: Age) -> bool:
        months = age.in_months
        return months >= self.min_months and (self.max_months is None or months <= self.max_months)


class LengthRange(BaseModel):
    """Une plage publiée, dans l’unité de la source ; `low` manque pour « au plus »."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    low: PlainDecimal | None = None
    high: PlainDecimal
    unit: LengthUnit

    @model_validator(mode="after")
    def _low_is_not_above_the_high(self) -> Self:
        if self.low is not None and self.low > self.high:
            raise ValueError("low ne peut pas dépasser high")
        return self

    @property
    def low_length(self) -> Length | None:
        return None if self.low is None else Length(value=self.low, unit=self.unit)

    @property
    def high_length(self) -> Length:
        return Length(value=self.high, unit=self.unit)


class ReferenceLength(BaseModel):
    """Une valeur publiée, dans l’unité de la source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: PlainDecimal
    unit: LengthUnit

    @property
    def length(self) -> Length:
        return Length(value=self.value, unit=self.unit)


class ReferenceMeasurement(SourcedEntry):
    """Une ligne de table : tour de tête (plage) ou hauteur (valeur), avec sa source.

    `age` manque pour une ligne sans âge chiffré (ADR 0020 : « Newborn », « Adult Man »…) ;
    `label` garde le libellé d’origine. `sex` n’est renseigné que pour une plage adulte.
    """

    quantity: Quantity
    label: str | None = None
    age: AgeBounds | None = None
    sex: Sex | None = None
    span: LengthRange | None = None
    value: ReferenceLength | None = None

    @model_validator(mode="after")
    def _has_the_shape_of_its_quantity(self) -> Self:
        if self.quantity is Quantity.HEAD_CIRCUMFERENCE:
            if self.span is None or self.value is not None:
                raise ValueError("un tour de tête porte `span`, pas `value`")
        elif self.value is None or self.span is not None:
            raise ValueError("une hauteur porte `value`, pas `span`")
        return self
