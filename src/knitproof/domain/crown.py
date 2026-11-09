"""Calotte du bonnet : ses rangs et ce qu’il en reste (CLA-68, ADR 0019)."""

from pydantic import BaseModel, ConfigDict, Field

from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.notice import Notice
from knitproof.domain.pattern import Round
from knitproof.domain.question import PendingQuestion


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


class CrownReview(BaseModel):
    """La calotte, ou son absence, avec les avis et les questions qui la concernent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    crown: Crown | None
    notices: tuple[Notice, ...] = ()
    questions: tuple[PendingQuestion, ...] = ()
