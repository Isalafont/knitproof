"""Passage du bord au corps par un rang d’ajustement (CLA-103, ADR 0025)."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.pattern import Round


class TransitionRejection(StrEnum):
    TOO_MANY_DECREASES = "too_many_decreases"
    TOO_MANY_INCREASES = "too_many_increases"


class Transition(BaseModel):
    """Du bord au corps : un rang d’ajustement, ou aucun si les comptes sont égaux."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_stitches: StrictPositiveInt
    body_stitches: StrictPositiveInt
    adjustment_round: Round | None

    @model_validator(mode="after")
    def _round_bridges_edge_to_body(self) -> Self:
        round_ = self.adjustment_round
        if round_ is None:
            if self.edge_stitches != self.body_stitches:
                raise ValueError(
                    "un rang d’ajustement est requis quand le bord et le corps diffèrent"
                )
            return self
        if self.edge_stitches == self.body_stitches:
            raise ValueError("aucun rang d’ajustement quand le bord et le corps sont égaux")
        if round_.start != 1 or round_.end is not None:
            raise ValueError("le rang d’ajustement est un seul rang, le rang 1 de la transition")
        if (round_.consumes, round_.produces, round_.stated_count) != (
            self.edge_stitches,
            self.body_stitches,
            self.body_stitches,
        ):
            raise ValueError("le rang d’ajustement doit consommer le bord et produire le corps")
        return self


class TransitionRefusal(BaseModel):
    """Écart impossible à franchir en un seul rang ; `limit` : corps atteignable le plus proche."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_stitches: StrictPositiveInt
    body_stitches: StrictPositiveInt
    reason: TransitionRejection
    limit: StrictPositiveInt
