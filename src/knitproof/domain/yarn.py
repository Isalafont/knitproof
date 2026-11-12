"""La laine de référence : composition, étiquette du fabricant, échantillons (CLA-121, ADR 0030).

Une laine est un produit. Son comportement vient d’un échantillon tricoté, jamais de ses fibres.
"""

import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from knitproof.domain.fiber import FiberComposition
from knitproof.domain.gauge import LabelGauge
from knitproof.domain.measure import PlainDecimal, SwatchMeasurement
from knitproof.domain.needle import NeedleSize
from knitproof.domain.provenance import Provenance, SourcedEntry, SourceKind, _only_a_date

type Text = Annotated[str, StringConstraints(min_length=1)]
type NeedleSizes = Annotated[tuple[NeedleSize, ...], Field(min_length=1, max_length=2)]


class YarnLabel(BaseModel):
    """Ce que le fabricant publie ; chaque valeur est facultative, aucune n’est inventée.

    Les aiguilles sont une taille ou deux (une fourchette), reprises dans le système du fabricant.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    gauge: LabelGauge | None = None
    needles: NeedleSizes | None = None
    length_m: PlainDecimal | None = None
    weight_g: PlainDecimal | None = None
    care: str | None = None
    yarn_weight: Text | None = None


class YarnSwatch(BaseModel):
    """Un échantillon tricoté par la personne : mesure avant et après blocage, aiguilles, point."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    before: SwatchMeasurement | None = None
    after: SwatchMeasurement | None = None
    needle: NeedleSize
    stitch: Text
    knitted_on: Annotated[datetime.date, BeforeValidator(_only_a_date)]
    source: Provenance

    @model_validator(mode="after")
    def _has_a_measure(self) -> Self:
        if self.before is None and self.after is None:
            raise ValueError("une mesure avant ou après blocage est attendue (au moins l’une)")
        return self

    @model_validator(mode="after")
    def _comes_from_a_user_swatch(self) -> Self:
        if self.source.kind is not SourceKind.USER_SWATCH:
            raise ValueError("la source d’un échantillon est de sorte user_swatch")
        return self


class YarnFamily(BaseModel):
    """La famille d’une laine : sa fibre majoritaire et son traitement superwash (ADR 0031)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fiber: Text
    superwash: bool


class Yarn(SourcedEntry):
    """Une laine : marque, nom, composition, superwash (`None` si non publié), étiquette.

    `swatches` reste vide tant qu’aucun échantillon n’a été tricoté ; aucun calcul ne le lit ici.
    """

    brand: Text
    name: Text
    composition: FiberComposition
    superwash: bool | None
    label: YarnLabel
    swatches: tuple[YarnSwatch, ...] = ()

    @property
    def family(self) -> YarnFamily | None:
        """Fibre majoritaire et superwash ; `None` si égalité de parts ou superwash absent."""
        if self.superwash is None:
            return None
        top = max(part.percent for part in self.composition.parts)
        leaders = [part for part in self.composition.parts if part.percent == top]
        if len(leaders) != 1:
            return None
        return YarnFamily(fiber=leaders[0].fiber, superwash=self.superwash)
