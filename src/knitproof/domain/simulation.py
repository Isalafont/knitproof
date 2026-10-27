"""Résultat de la simulation d’un patron."""

from pydantic import BaseModel, ConfigDict, PositiveInt

from knitproof.domain.finding import Finding


class RoundCount(BaseModel):
    """Mailles sur les aiguilles à la fin d’un tour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    round: PositiveInt
    stitches: PositiveInt


class Simulation(BaseModel):
    """Comptes tour par tour, et le constat qui a arrêté la simulation s’il y en a un."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    counts: tuple[RoundCount, ...]
    halted: Finding | None = None
