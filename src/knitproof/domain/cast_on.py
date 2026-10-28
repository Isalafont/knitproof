"""Point déclaré et résultat du montage (CLA-65, ADR 0007 et 0015)."""

from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from knitproof.domain.integers import StrictNonNegativeInt, StrictPositiveInt
from knitproof.domain.measure import Length


class RoundingRule(StrEnum):
    NEAREST_TIE_DOWN = "nearest_tie_down"


class StitchMultiple(BaseModel):
    """Multiple et reste du point : 4n + 2 s’écrit (4, 2)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repeat_multiple: StrictPositiveInt
    repeat_offset: StrictNonNegativeInt

    @model_validator(mode="after")
    def _offset_is_below_multiple(self) -> Self:
        if self.repeat_offset >= self.repeat_multiple:
            raise ValueError("le reste doit être inférieur au multiple")
        return self

    def accepts(self, stitches: int) -> bool:
        return stitches % self.repeat_multiple == self.repeat_offset


class CastOnResult(BaseModel):
    """Montage calculé, avec la trace de son arrondi (ADR 0007)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target: Length
    raw_stitches: Decimal
    stitches: StrictPositiveInt
    rounding_rule: RoundingRule
    finished_cm: Decimal


class CastOnRejection(StrEnum):
    STITCH_MULTIPLE_NOT_RESPECTED = "stitch_multiple_not_respected"
    DIFFERS_FROM_CALCULATION = "differs_from_calculation"


class CastOnCheck(BaseModel):
    """Contrôle d’un nombre proposé : raisons du rejet et largeur finie."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    proposed: StrictPositiveInt
    expected: StrictPositiveInt
    reasons: tuple[CastOnRejection, ...]
    proposed_finished_cm: Decimal

    @property
    def accepted(self) -> bool:
        return not self.reasons
