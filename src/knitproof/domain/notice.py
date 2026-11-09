"""Avis d’information : ce qui n’est pas un écart prouvé (CLA-67, ADR 0021 §5).

`Finding` ne porte que des erreurs du moteur ; une taille hors table est acceptée, avec un avis.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class NoticeStatus(StrEnum):
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"


class NoticeCode(StrEnum):
    UNKNOWN_NEEDLE_SIZE = "unknown_needle_size"


class Notice(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: NoticeStatus
    code: NoticeCode
    text: str
