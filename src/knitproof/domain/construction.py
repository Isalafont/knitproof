"""Valeurs de construction du bonnet : calotte et magic loop (CLA-67, ADR 0019 et 0023)."""

from typing import Literal, Self

from pydantic import model_validator

from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.provenance import SourcedEntry
from knitproof.domain.reference import ReferenceLength


class CrownRule(SourcedEntry):
    """Les seuils de la calotte (ADR 0019) : décisions d’Isabelle, sans source publiée."""

    decreases_per_round: StrictPositiveInt
    last_round_below: StrictPositiveInt
    min_cast_on: StrictPositiveInt
    every_round_last: StrictPositiveInt

    @model_validator(mode="after")
    def _last_round_threshold_is_below_the_minimum_cast_on(self) -> Self:
        if self.last_round_below > self.min_cast_on:
            raise ValueError("last_round_below ne peut pas dépasser min_cast_on")
        return self


class MagicLoopAdvice(SourcedEntry):
    """Câble conseillé pour le magic loop (ADR 0023 §6) : un conseil, jamais une règle calculée."""

    role: Literal["advice"] = "advice"
    magic_loop_cable: ReferenceLength
