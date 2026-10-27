"""Opérations d’un tour : mailles consommées et produites."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    NonNegativeInt,
    PositiveInt,
    Tag,
    model_validator,
)

from knitproof.domain.location import SourceLocation


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


class Round(BaseModel):
    """Un tour, ou une plage de tours qui répètent les mêmes opérations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: PositiveInt
    end: PositiveInt | None = None
    ops: tuple[Op, ...] = Field(min_length=1)
    stated_count: NonNegativeInt | None = None
    location: SourceLocation | None = None

    @property
    def last(self) -> int:
        return self.start if self.end is None else self.end

    @property
    def consumes(self) -> int:
        return sum(op.consumes for op in self.ops)

    @property
    def produces(self) -> int:
        return sum(op.produces for op in self.ops)

    @model_validator(mode="after")
    def _ends_after_start(self) -> Self:
        if self.end is not None and self.end < self.start:
            raise ValueError(f"le tour {self.start} se termine avant son début ({self.end})")
        return self


class Pattern(BaseModel):
    """Un patron : montage et tours contigus à partir du tour 1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cast_on: PositiveInt
    rounds: tuple[Round, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _rounds_are_contiguous(self) -> Self:
        expected = 1
        for round_ in self.rounds:
            if round_.start != expected:
                raise ValueError(f"tour {round_.start} : le tour attendu est le tour {expected}")
            expected = round_.last + 1
        return self
