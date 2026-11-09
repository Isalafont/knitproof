"""Calotte du bonnet : ses rangs et ce qu’il en reste (CLA-68, ADR 0019)."""

from pydantic import BaseModel, ConfigDict, Field

from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.pattern import Round


class Crown(BaseModel):
    """Les rangs de la calotte, numérotés depuis 1 : l’assemblage les décale."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: StrictPositiveInt
    rounds: tuple[Round, ...] = Field(min_length=1)
    decrease_rounds: StrictPositiveInt
    remaining: StrictPositiveInt

    @property
    def round_count(self) -> int:
        return self.rounds[-1].last
