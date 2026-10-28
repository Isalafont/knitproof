"""Longueurs et mesure de l’échantillon (CLA-65, ADR 0007 et 0015)."""

from decimal import ROUND_HALF_EVEN, Context, Decimal, Inexact, Rounded
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

INCH_IN_CM = Decimal("2.54")

# Produits : une exception plutôt qu’un arrondi silencieux (ADR 0015).
EXACT = Context(prec=28, traps=[Inexact, Rounded])
# Quotients : 28 chiffres significatifs, pour la trace seulement (ADR 0015).
DIVISION = Context(prec=28, rounding=ROUND_HALF_EVEN)


def _refuse_float(value: object) -> object:
    if isinstance(value, float):
        raise ValueError("float refusé : écrire la valeur en Decimal ou en texte")
    return value


# Au plus 5 chiffres en écriture décimale, zéros finaux retirés ; les zéros entre
# la virgule et le premier chiffre comptent.
PositiveDecimal = Annotated[Decimal, BeforeValidator(_refuse_float), Field(gt=0, max_digits=5)]


class LengthUnit(StrEnum):
    CM = "cm"
    IN = "in"


class Length(BaseModel):
    """Une longueur, avec son unité d’origine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: PositiveDecimal
    unit: LengthUnit

    @property
    def in_cm(self) -> Decimal:
        if self.unit is LengthUnit.IN:
            return EXACT.multiply(self.value, INCH_IN_CM)
        return self.value


class SwatchMeasurement(BaseModel):
    """Mailles comptées sur une largeur d’échantillon (demi-mailles admises)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: PositiveDecimal
    width: Length

    @property
    def stitches_per_10_cm(self) -> Decimal:
        return DIVISION.divide(EXACT.multiply(self.stitches, Decimal(10)), self.width.in_cm)
