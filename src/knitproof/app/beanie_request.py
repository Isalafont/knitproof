"""La demande de bonnet en YAML : format figé, aiguilles lues à la porte (CLA-69, CLA-104).

La demande garde les unités et les provenances saisies ; l’aisance en % s’applique ici pour
donner le tour visé, le seul calcul de la porte (ADR 0024).
"""

import re
from decimal import Decimal, Inexact, Rounded
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

from knitproof.app.errors import condense
from knitproof.domain.beanie import BeanieSpecification
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.ease import Ease, EaseUnit, EdgeStitch
from knitproof.domain.gauge import LabelGauge
from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.measure import EXACT, Length, LengthUnit, SwatchMeasurement
from knitproof.domain.needle import KnittingMethod, Needle

_NEEDLE_FORMS = "« 4 mm », « US 6 » ou « US 6 (4 mm) »"
_NEEDLE_SIZE = re.compile(
    r"(?P<system>us|uk|jp)\s*(?P<original>[^\s()]+)(?:\s*\(\s*(?P<mm>[0-9]+(?:[.,][0-9]+)?)\s*mm\s*\))?",
    re.IGNORECASE,
)
_MM_ONLY = re.compile(r"(?P<mm>[0-9]+(?:[.,][0-9]+)?)\s*mm", re.IGNORECASE)
_PERCENT = Decimal(100)


class Origin(StrEnum):
    """D’où vient une valeur saisie."""

    MEASURED = "measured"
    ENTERED = "entered"


class ProposalOrigin(StrEnum):
    LLM_ONLY = "llm_only"


class EnteredLength(Length):
    provenance: Origin


class EnteredEase(Ease):
    provenance: Origin


class EnteredStitchMultiple(StitchMultiple):
    provenance: Origin


class ProposedCastOn(BaseModel):
    """Un montage proposé, à contrôler : le moteur ne le prend jamais pour acquis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: StrictPositiveInt
    origin: ProposalOrigin


def _read_needle(value: object) -> object:
    """« 4 mm », « US 6 », « US 6 (4 mm) » : la notation se découpe avant `NeedleSize`."""
    if not isinstance(value, dict) or not isinstance(value.get("size"), str):
        return value
    return {**value, "size": _needle_size(value["size"])}


def _needle_size(text: str) -> dict[str, str]:
    stripped = text.strip()
    if found := _MM_ONLY.fullmatch(stripped):
        return {"system": "mm", "original": found["mm"]}
    if found := _NEEDLE_SIZE.fullmatch(stripped):
        size = {"system": found["system"].lower(), "original": found["original"]}
        return {**size, "mm": found["mm"].replace(",", ".")} if found["mm"] else size
    raise ValueError(f"taille d’aiguille « {text} » non reconnue : écrire {_NEEDLE_FORMS}")


type RequestNeedle = Annotated[Needle, BeforeValidator(_read_needle)]


class RowsSource(BaseModel):
    """D’où vient la jauge en rangs, quand ce n’est pas une mesure de la personne."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reference: str = Field(min_length=1, pattern=r"\S")
    to_verify: bool = False


class RequestSwatchMeasurement(SwatchMeasurement):
    """Un échantillon mesuré, dont la jauge en rangs peut citer sa source."""

    rows_source: RowsSource | None = None


class RequestSwatch(BaseModel):
    """L’échantillon : après blocage, avant blocage, ou d’état de blocage inconnu.

    Au moins une mesure ; `unknown_blocking` est exclusif des deux autres : on répond à la
    question « l’as-tu bloqué ? » en renommant la clé (CLA-66).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitch: EdgeStitch | None = None
    needle: RequestNeedle
    before_blocking: RequestSwatchMeasurement | None = None
    after_blocking: RequestSwatchMeasurement | None = None
    unknown_blocking: RequestSwatchMeasurement | None = None

    @model_validator(mode="after")
    def _one_coherent_set_of_measures(self) -> Self:
        known = (self.before_blocking, self.after_blocking)
        if self.unknown_blocking is None and all(measure is None for measure in known):
            raise ValueError(
                "au moins une mesure : after_blocking, before_blocking ou unknown_blocking"
            )
        if self.unknown_blocking is not None and any(measure is not None for measure in known):
            raise ValueError(
                "unknown_blocking ne va pas avec after_blocking ni before_blocking : "
                "renommer la clé selon la réponse"
            )
        return self


class BeanieRequest(BaseModel):
    """Ce que demande la personne, tel qu’écrit dans le fichier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    head_circumference: EnteredLength
    ease: EnteredEase
    swatch: RequestSwatch | None = None
    label_gauge: LabelGauge | None = None
    needles: tuple[RequestNeedle, ...]
    stitch_multiple: EnteredStitchMultiple
    total_height: EnteredLength | None = None
    brim_height: EnteredLength | None = None
    folded_brim: bool = False
    worked: KnittingMethod = KnittingMethod.ROUND
    proposed_cast_on: ProposedCastOn | None = None

    @model_validator(mode="after")
    def _is_computable(self) -> Self:
        """Le tour visé et la spécification se construisent : sinon, une erreur de saisie."""
        for build in (lambda: self.circumference, lambda: self.specification):
            try:
                build()
            except ValidationError as error:
                raise ValueError(_reasons(error)) from error
            except (Inexact, Rounded) as error:
                raise ValueError("nombre trop grand ou trop précis") from error
        return self

    @property
    def circumference(self) -> Length:
        """Le tour visé : tour de tête et aisance, calculés exactement (ADR 0007)."""
        head, ease = self.head_circumference, self.ease
        if ease.unit is EaseUnit.PERCENT:
            value = EXACT.divide(EXACT.multiply(head.value, _PERCENT + ease.value), _PERCENT)
            return Length(value=value, unit=head.unit)
        return Length(value=EXACT.add(head.in_cm, ease.value), unit=LengthUnit.CM)

    @property
    def multiple(self) -> StitchMultiple:
        return StitchMultiple(
            repeat_multiple=self.stitch_multiple.repeat_multiple,
            repeat_offset=self.stitch_multiple.repeat_offset,
        )

    @property
    def specification(self) -> BeanieSpecification:
        return BeanieSpecification(
            total_height=_plain(self.total_height),
            brim_height=_plain(self.brim_height),
            folded_brim=self.folded_brim,
            worked=self.worked,
            needles=self.needles,
        )


def _plain(length: EnteredLength | None) -> Length | None:
    return None if length is None else Length(value=length.value, unit=length.unit)


def _reasons(error: ValidationError) -> str:
    return " ; ".join(condense(error, None).splitlines())
