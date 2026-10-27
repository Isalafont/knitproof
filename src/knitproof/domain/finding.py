"""Constats du moteur sur un patron."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveInt

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
    round: PositiveInt
    expected: NonNegativeInt
    actual: NonNegativeInt
    location: SourceLocation | None = None
