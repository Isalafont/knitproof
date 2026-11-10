"""Jauge d’étiquette et jauge résolue (CLA-66, ADR 0008).

`ResolvedGauge` est la seule structure de résolution : la jauge retenue (ou aucune), d’où
elle vient, les avis et les questions en attente.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from knitproof.domain.measure import Length, PositiveDecimal, SwatchMeasurement
from knitproof.domain.notice import Notice
from knitproof.domain.question import PendingQuestion


class GaugeRange(BaseModel):
    """Une fourchette de l’étiquette ; aucun milieu n’est calculé."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    low: PositiveDecimal
    high: PositiveDecimal

    @model_validator(mode="after")
    def _low_is_below_high(self) -> Self:
        if self.low >= self.high:
            raise ValueError("la borne basse doit être inférieure à la borne haute")
        return self


# `left_to_right` : la doc de pydantic garantit cet ordre, le mode « smart » peut changer.


class LabelGauge(BaseModel):
    """La jauge du fabricant : mailles sur une largeur, rangs sur une hauteur (facultatifs)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: PositiveDecimal | GaugeRange = Field(union_mode="left_to_right")
    width: Length
    rows: PositiveDecimal | GaugeRange | None = Field(default=None, union_mode="left_to_right")
    height: Length | None = None

    @model_validator(mode="after")
    def _rows_and_height_go_together(self) -> Self:
        if (self.rows is None) != (self.height is None):
            raise ValueError("les rangs et leur hauteur vont ensemble : deux valeurs ou aucune")
        return self


class GaugeSource(StrEnum):
    BLOCKED = "blocked"
    UNBLOCKED = "unblocked"
    LABEL = "label"


class ResolvedGauge(BaseModel):
    """La jauge retenue et sa source ; sans jauge, des questions et pas de source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    gauge: SwatchMeasurement | None
    source: GaugeSource | None
    notices: tuple[Notice, ...] = ()
    questions: tuple[PendingQuestion, ...] = ()

    @model_validator(mode="after")
    def _source_goes_with_gauge(self) -> Self:
        if (self.gauge is None) != (self.source is None):
            raise ValueError("la source de la jauge va avec la jauge : les deux ou aucune")
        return self
