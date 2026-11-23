"""La lecture d’une demande de bonnet, telle que le texte la dit, et sa conversion (CLA-200).

Le modèle lit ; le code convertit en entrées du moteur, en calcul exact. Aucun champ n’est
requis : ce que le texte ne dit pas reste vide, et `reading_inputs` nomme ce qui manque.
"""

from decimal import Decimal, Inexact, Rounded
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.gauge import LabelGauge
from knitproof.domain.measure import EXACT, Length, LengthUnit, SwatchMeasurement
from knitproof.domain.needle import KnittingMethod
from knitproof.domain.provenance import Provenance, SourceKind


def _read_number(value: object) -> object:
    """Un nombre JSON (entier ou flottant) ou un décimal en chaîne ; jamais un booléen."""
    if isinstance(value, bool):
        raise ValueError("un nombre est attendu, pas un booléen")
    if isinstance(value, float):
        return Decimal(str(value))
    return value


# Le schéma annonce `number` : un nombre JSON passe, converti par `Decimal(str(x))`.
type ReadDecimal = Annotated[Decimal, BeforeValidator(_read_number), Field(gt=0, max_digits=5)]


class ReadEdge(StrEnum):
    """Le bord, nommé comme le texte l’écrit."""

    RIB_1X1 = "rib_1x1"
    RIB_2X2 = "rib_2x2"
    ROLLED_STOCKINETTE = "rolled_stockinette"
    GARTER = "garter"


# Définition du point : côtes 1/1 sur 2, côtes 2/2 sur 4 (signés par CLA-188) ; garter à confirmer.
EDGE_MULTIPLES: dict[ReadEdge, int] = {
    ReadEdge.RIB_1X1: 2,
    ReadEdge.RIB_2X2: 4,
    ReadEdge.ROLLED_STOCKINETTE: 1,
    ReadEdge.GARTER: 1,
}


class ReadLength(BaseModel):
    """Une longueur avec son unité, comme écrite."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: ReadDecimal
    unit: LengthUnit


class ReadGauge(BaseModel):
    """Des mailles sur une largeur, comme écrites."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: ReadDecimal
    width: ReadLength


class BeanieReading(BaseModel):
    """Ce que le texte d’une demande dit ; `None` pour ce qu’il ne dit pas.

    `smaller_than_head` est l’écart dit, positif (« 5 cm de moins » donne 5 cm).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    head_circumference: ReadLength | None = None
    smaller_than_head: ReadLength | None = None
    finished_circumference: ReadLength | None = None
    gauge_after_blocking: ReadGauge | None = None
    gauge_before_blocking: ReadGauge | None = None
    gauge_unknown_blocking: ReadGauge | None = None
    label_gauge: ReadGauge | None = None
    needle_mm: tuple[ReadDecimal, ...] = ()
    edge: ReadEdge | None = None
    worked: KnittingMethod | None = None


class ReadingIncomplete(BaseModel):
    """Un champ requis manque ou ne se convertit pas : `field` le nomme."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    reason: str


class ReadingInputs(BaseModel):
    """Les entrées du moteur tirées d’une lecture : tour visé, mesures, point."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target: Length
    multiple: StitchMultiple
    blocked: SwatchMeasurement | None = None
    unblocked: SwatchMeasurement | None = None
    unknown: SwatchMeasurement | None = None
    label: LabelGauge | None = None


class ReadingRecord(BaseModel):
    """Une lecture et sa provenance : une inférence de modèle, à vérifier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reading: BeanieReading
    provenance: Provenance

    @model_validator(mode="after")
    def _is_a_model_inference(self) -> Self:
        if self.provenance.kind is not SourceKind.MODEL_INFERENCE:
            raise ValueError("une lecture a pour provenance model_inference")
        return self


def reading_inputs(reading: BeanieReading) -> ReadingInputs | ReadingIncomplete:
    """Convertit une lecture en entrées du moteur, ou nomme le champ qui manque."""
    head = reading.head_circumference
    if head is None:
        return ReadingIncomplete(field="head_circumference", reason="absent")
    if reading.edge is None:
        return ReadingIncomplete(field="edge", reason="absent")
    target = _target(reading, head)
    if isinstance(target, ReadingIncomplete):
        return target
    return ReadingInputs(
        target=target,
        multiple=StitchMultiple(repeat_multiple=EDGE_MULTIPLES[reading.edge], repeat_offset=0),
        blocked=_swatch(reading.gauge_after_blocking),
        unblocked=_swatch(reading.gauge_before_blocking),
        unknown=_swatch(reading.gauge_unknown_blocking),
        label=_label(reading.label_gauge),
    )


def _target(reading: BeanieReading, head: ReadLength) -> Length | ReadingIncomplete:
    gap, finished = reading.smaller_than_head, reading.finished_circumference
    if gap is None and finished is None:
        return ReadingIncomplete(field="smaller_than_head", reason="ni écart ni tour fini visé")
    if gap is not None and finished is not None:
        return ReadingIncomplete(
            field="finished_circumference",
            reason="écart et tour fini à la fois : un seul est attendu",
        )
    try:
        if finished is not None:
            return _cm(finished.value, finished.unit)
        assert gap is not None
        head_cm = _cm(head.value, head.unit).value
        return Length(
            value=EXACT.subtract(head_cm, _cm(gap.value, gap.unit).value), unit=LengthUnit.CM
        )
    except (ValidationError, Inexact, Rounded):
        name = "finished_circumference" if finished is not None else "smaller_than_head"
        return ReadingIncomplete(field=name, reason="tour visé non calculable")


def _cm(value: Decimal, unit: LengthUnit) -> Length:
    return Length(value=Length(value=value, unit=unit).in_cm, unit=LengthUnit.CM)


def _length(length: ReadLength) -> Length:
    return Length(value=length.value, unit=length.unit)


def _swatch(gauge: ReadGauge | None) -> SwatchMeasurement | None:
    if gauge is None:
        return None
    return SwatchMeasurement(stitches=gauge.stitches, width=_length(gauge.width))


def _label(gauge: ReadGauge | None) -> LabelGauge | None:
    if gauge is None:
        return None
    return LabelGauge(stitches=gauge.stitches, width=_length(gauge.width))
