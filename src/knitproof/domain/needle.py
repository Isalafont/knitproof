"""Aiguilles dans leur système d’origine, sans table de correspondance (CLA-104, ADR 0016)."""

import re
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from knitproof.domain.measure import Length, PlainDecimal, PositiveDecimal
from knitproof.domain.provenance import SourcedEntry


class NeedleSystem(StrEnum):
    MM = "mm"
    US = "us"
    UK = "uk"
    JP = "jp"


# Le marqueur du système déclaré est toléré ; celui d’un autre système n’est jamais reconnu.
_MARKERS: dict[NeedleSystem, re.Pattern[str]] = {
    NeedleSystem.MM: re.compile(r"(?P<value>.+?)(?:\s*mm)?", re.IGNORECASE),
    NeedleSystem.US: re.compile(r"(?:us\s*)?(?P<value>.+)", re.IGNORECASE),
    NeedleSystem.UK: re.compile(r"(?:uk\s*)?(?P<value>.+)", re.IGNORECASE),
    NeedleSystem.JP: re.compile(r"(?:jp\s*)?(?P<value>.+?)(?:\s*号)?", re.IGNORECASE),
}

# `[0-9]` en clair et non `\d` : un chiffre pleine largeur est refusé.
_FORMS: dict[NeedleSystem, re.Pattern[str]] = {
    NeedleSystem.MM: re.compile(r"[0-9]+(?:[.,][0-9]+)?"),
    NeedleSystem.US: re.compile(r"0+|[1-9][0-9]*(?:\.[0-9]+|½|¾)?"),
    NeedleSystem.UK: re.compile(r"0+|[1-9][0-9]*(?:\.[0-9]+|½|¾)?"),
    NeedleSystem.JP: re.compile(r"0|[1-9][0-9]*"),
}

_FRACTIONS = {"½": ".5", "¾": ".75"}

_MM_VALUE = TypeAdapter(PositiveDecimal)


class NeedleSize(BaseModel):
    """Une taille dans son système ; le `mm` n’est jamais calculé d’un autre système."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    system: NeedleSystem
    original: str
    mm: PositiveDecimal | None = None

    @model_validator(mode="after")
    def _is_well_formed_and_consistent(self) -> Self:
        self._normalize()
        if self.system is NeedleSystem.MM and self.mm is not None and self.mm != self.known_mm:
            raise ValueError("le mm saisi contredit la notation en mm")
        return self

    @property
    def normalized(self) -> str:
        """Valeur à l’intérieur du système : « 00 » reste distinct de « 0 » en us et uk.

        En US, « 2.5 », « 2.50 » et « 2½ » sont égaux, « 10¾ » vaut « 10.75 » (ADR 0021,
        décision 8) ; UK, comparé par notation, n’a pas cette égalité.
        """
        value = self._normalize()
        if self.system is NeedleSystem.MM:
            return format(self._mm_value(value).normalize(), "f")
        if self.system is NeedleSystem.US and not value.startswith("0"):
            return self._us_decimal(value)
        return value

    def _us_decimal(self, value: str) -> str:
        for fraction, decimals in _FRACTIONS.items():
            value = value.replace(fraction, decimals)
        return format(Decimal(value).normalize(), "f")

    @property
    def known_mm(self) -> Decimal | None:
        """Le mm lu dans la notation (système mm) ou saisi ; jamais converti."""
        if self.system is NeedleSystem.MM:
            return self._mm_value(self._normalize())
        return self.mm

    def _normalize(self) -> str:
        found = _MARKERS[self.system].fullmatch(self.original.strip())
        value = found["value"].strip() if found else ""
        if not _FORMS[self.system].fullmatch(value):
            raise ValueError(f"taille « {self.original} » mal formée pour le système {self.system}")
        if self.system is NeedleSystem.MM:
            self._mm_value(value)
        return value

    def _mm_value(self, value: str) -> Decimal:
        try:
            return _MM_VALUE.validate_python(Decimal(value.replace(",", ".")))
        except ValidationError as error:
            raise ValueError(f"taille en mm invalide : {error.errors()[0]['msg']}") from error


class NeedleKind(StrEnum):
    STRAIGHT = "straight"
    CIRCULAR = "circular"
    DOUBLE_POINTED = "double_pointed"


class NeedleMaterial(StrEnum):
    """Aluminium, acier, nickel et laiton restent `metal` ; le verre est `other`."""

    METAL = "metal"
    WOOD = "wood"
    BAMBOO = "bamboo"
    PLASTIC = "plastic"
    CARBON = "carbon"
    OTHER = "other"


class KnittingMethod(StrEnum):
    FLAT = "flat"
    ROUND = "round"


class Needle(BaseModel):
    """Taille, type et matière ; la longueur de câble n’existe que pour une circulaire."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    size: NeedleSize
    kind: NeedleKind
    cable_length: Length | None = None
    material: NeedleMaterial | None = None

    @model_validator(mode="after")
    def _cable_only_on_circular(self) -> Self:
        if self.cable_length is not None and self.kind is not NeedleKind.CIRCULAR:
            raise ValueError("une longueur de câble n’existe que pour une aiguille circulaire")
        return self


class NeedleMismatch(StrEnum):
    SIZE_DIFFERS = "size_differs"
    SIZES_NOT_COMPARABLE = "sizes_not_comparable"
    MATERIAL_DIFFERS = "material_differs"


class NeedleCheck(BaseModel):
    """Aiguilles de l’échantillon et du projet, avec les raisons de l’avertissement."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    swatch: Needle
    project: Needle
    reasons: tuple[NeedleMismatch, ...]

    @property
    def matches(self) -> bool:
        return not self.reasons


class NeedleTableRow(SourcedEntry):
    """Une ligne des tables de l’ADR 0021 : une taille US, UK ou JP et ses mm publiés.

    Un ou deux mm : le Craft Yarn Council fait correspondre 4 et 4,25 mm à US 6. Le système
    `mm` n’a pas de table : un mm est une mesure.
    """

    system: NeedleSystem
    size: str
    mm: tuple[PlainDecimal, ...] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def _is_a_size_of_a_tabulated_system(self) -> Self:
        if self.system is NeedleSystem.MM:
            raise ValueError("le système mm n’a pas de table")
        NeedleSize(system=self.system, original=self.size)
        return self
