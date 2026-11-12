"""Aisance saisie (CLA-112) et aisance de référence tirée d’une source (CLA-67, ADR 0024)."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.measure import PlainDecimal, SwatchMeasurement, _refuse_float
from knitproof.domain.provenance import Provenance, SourcedEntry
from knitproof.domain.reference import LengthRange, ReferenceLength

# Au plus 5 chiffres, le signe n’en compte pas.
SignedDecimal = Annotated[Decimal, BeforeValidator(_refuse_float), Field(max_digits=5)]


class EaseUnit(StrEnum):
    PERCENT = "percent"
    CM = "cm"


class Ease(BaseModel):
    """Une aisance, avec son unité d’origine ; la valeur de référence est en % (ADR 0024 §2)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: SignedDecimal
    unit: EaseUnit


class Fit(StrEnum):
    """L’ajustement voulu (ADR 0024 §3)."""

    FITTED = "fitted"
    LOOSE = "loose"


class EdgeStitch(StrEnum):
    """Le point du bord, là où se mesure l’aisance (ADR 0024 §1)."""

    STOCKINETTE = "stockinette"
    RIB_1X1 = "rib_1x1"
    RIB_2X2 = "rib_2x2"
    GARTER = "garter"


class EaseRole(StrEnum):
    """Une source propose une valeur, ou reste un repère que le moteur montre sans la compter."""

    PROPOSAL = "proposal"
    LANDMARK = "landmark"


class SwatchSpec(BaseModel):
    """L’échantillon publié d’une source : mailles pour une largeur, unité d’origine, point."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: PlainDecimal
    width: ReferenceLength
    stitch: EdgeStitch

    @property
    def measurement(self) -> SwatchMeasurement:
        return SwatchMeasurement(stitches=self.stitches, width=self.width.length)


class EaseSize(BaseModel):
    """Une taille de la source : plage de tête, et montage ou tour du bord publié."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    head: LengthRange
    cast_on: StrictPositiveInt | None = None
    brim_circumference: ReferenceLength | None = None

    @model_validator(mode="after")
    def _has_a_head_range_and_one_circumference(self) -> Self:
        if self.head.low is None:
            raise ValueError("head.low manque : la plage de tête a deux bornes")
        if (self.cast_on is None) == (self.brim_circumference is None):
            raise ValueError("une taille porte cast_on ou brim_circumference, pas les deux")
        return self


class EaseSource(SourcedEntry):
    """Les données brutes d’une source d’aisance, pour un couple (ajustement, point du bord).

    Le moteur en déduit le % (ADR 0024 §7) ; rien n’est stocké en %.
    """

    fit: Fit
    edge: EdgeStitch
    swatch: SwatchSpec | None = None
    yarns: tuple[str, ...] = ()
    role: EaseRole = EaseRole.PROPOSAL
    role_reason: str | None = None
    sizes: tuple[EaseSize, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _a_cast_on_needs_a_swatch(self) -> Self:
        if self.swatch is None and any(size.cast_on is not None for size in self.sizes):
            raise ValueError("un montage demande l’échantillon (swatch) de la source")
        return self

    @model_validator(mode="after")
    def _a_landmark_says_why(self) -> Self:
        if self.role is EaseRole.LANDMARK and not self.role_reason:
            raise ValueError("un repère (landmark) dit pourquoi : role_reason manque")
        return self


class BaseEase(SourcedEntry):
    """L’aisance de base, en %, décidée pour des bords et un point d’échantillon donnés.

    Elle vaut quand aucune source ne correspond (ADR 0031) ; elle n’est pas tirée d’un patron.
    """

    fit: Fit
    edges: tuple[EdgeStitch, ...] = Field(min_length=1)
    swatch_stitch: EdgeStitch
    value: SignedDecimal


_Percent = Annotated[Decimal, BeforeValidator(_refuse_float)]


class EaseProposal(BaseModel):
    """L’aisance proposée par une source, en %, avec sa plage et sa provenance « À VÉRIFIER ».

    Ce ne sont ni des `Ease` ni des `Length` : le quotient garde ses 28 chiffres (ADR 0015) ;
    l’arrondi de lecture revient à l’affichage.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    fit: Fit
    edge: EdgeStitch
    proposed: _Percent
    low: _Percent
    high: _Percent
    by_size: tuple[_Percent, ...]
    provenance: Provenance
