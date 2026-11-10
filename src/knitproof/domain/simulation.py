"""Résultat de la simulation d’un patron."""

from pydantic import BaseModel, ConfigDict

from knitproof.domain.finding import Finding
from knitproof.domain.integers import StrictPositiveInt


class RoundCount(BaseModel):
    """Mailles sur les aiguilles à la fin d’un rang."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    round: StrictPositiveInt
    stitches: StrictPositiveInt


class Simulation(BaseModel):
    """Comptes rang par rang, et le constat qui a arrêté la simulation s’il y en a un."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    counts: tuple[RoundCount, ...]
    halted: Finding | None = None
