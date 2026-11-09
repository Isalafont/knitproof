"""Avis d’information : ce qui n’est pas un écart prouvé (CLA-67, ADR 0021 §5).

`Finding` ne porte que des erreurs du moteur ; une taille hors table est acceptée, avec un avis.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from knitproof.domain.integers import StrictPositiveInt


class NoticeStatus(StrEnum):
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"


class NoticeCode(StrEnum):
    UNKNOWN_NEEDLE_SIZE = "unknown_needle_size"
    CROWN_ODD_STITCHES = "crown_odd_stitches"
    CROWN_TOO_SMALL = "crown_too_small"
    CROWN_LONE_STITCH = "crown_lone_stitch"
    NEEDLE_CHANGE = "needle_change"
    NEEDLE_TOO_LONG = "needle_too_long"
    BODY_TOO_SHORT = "body_too_short"
    CROWN_DEPTH_FLAT = "crown_depth_flat"


class Notice(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: NoticeStatus
    code: NoticeCode
    text: str
    round: StrictPositiveInt | None = None
