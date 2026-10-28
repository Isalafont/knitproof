"""Aiguilles dans leur système d’origine, sans table de correspondance (CLA-104, ADR 0016)."""

import re
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError, model_validator

from knitproof.domain.measure import PositiveDecimal


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
    NeedleSystem.US: re.compile(r"0+|[1-9][0-9]*½?"),
    NeedleSystem.UK: re.compile(r"0+|[1-9][0-9]*"),
    NeedleSystem.JP: re.compile(r"0|[1-9][0-9]*"),
}

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
        """Valeur à l’intérieur du système : « 00 » reste distinct de « 0 » en us et uk."""
        value = self._normalize()
        if self.system is NeedleSystem.MM:
            return format(self._mm_value(value).normalize(), "f")
        return value

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
