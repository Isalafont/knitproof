"""Opérations d’un tour : mailles consommées et produites."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Discriminator, Field, PositiveInt, Tag


class Stitch(StrEnum):
    """Opération simple, écrite nue en YAML."""

    K2TOG = "k2tog"
    M1 = "m1"

    @property
    def consumes(self) -> int:
        match self:
            case Stitch.K2TOG:
                return 2
            case Stitch.M1:
                return 0

    @property
    def produces(self) -> int:
        return 1


class Work(BaseModel):
    """Tricoter n mailles comme elles se présentent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work: PositiveInt

    @property
    def consumes(self) -> int:
        return self.work

    @property
    def produces(self) -> int:
        return self.work


class RepeatBlock(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    body: tuple["Op", ...] = Field(min_length=1)
    times: PositiveInt


class Repeat(BaseModel):
    """Répétition d’une suite d’opérations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repeat: RepeatBlock

    @property
    def consumes(self) -> int:
        return self.repeat.times * sum(op.consumes for op in self.repeat.body)

    @property
    def produces(self) -> int:
        return self.repeat.times * sum(op.produces for op in self.repeat.body)


def _op_kind(value: object) -> str | None:
    if isinstance(value, str | Stitch):
        return "stitch"
    if isinstance(value, dict):
        keys = set(value)
    elif isinstance(value, Work | Repeat):
        keys = set(type(value).model_fields)
    else:
        return None
    for kind in ("work", "repeat"):
        if kind in keys:
            return kind
    return None


type Op = Annotated[
    Annotated[Stitch, Tag("stitch")]
    | Annotated[Work, Tag("work")]
    | Annotated[Repeat, Tag("repeat")],
    Discriminator(_op_kind),
]
