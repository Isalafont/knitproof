"""Constats du moteur sur un patron."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from knitproof.domain.integers import StrictNonNegativeInt, StrictPositiveInt
from knitproof.domain.location import SourceLocation


class FindingStatus(StrEnum):
    ERROR = "error"


class FindingCode(StrEnum):
    COUNT_MISMATCH = "count_mismatch"
    REPEAT_NOT_FITTING = "repeat_not_fitting"


class Finding(BaseModel):
    """Un écart prouvé par le moteur : compte attendu, compte obtenu."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: FindingStatus
    code: FindingCode
    round: StrictPositiveInt
    expected: StrictNonNegativeInt
    actual: StrictNonNegativeInt
    location: SourceLocation | None = None
