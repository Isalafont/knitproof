"""Longueurs et mesure de l’échantillon (CLA-65, ADR 0007 et 0015)."""

import re
from decimal import ROUND_HALF_EVEN, Context, Decimal, Inexact, Rounded
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

INCH_IN_CM = Decimal("2.54")

# Produits : une exception plutôt qu’un arrondi silencieux (ADR 0015).
EXACT = Context(prec=28, traps=[Inexact, Rounded])
# Quotients : 28 chiffres significatifs, pour la trace seulement (ADR 0015).
DIVISION = Context(prec=28, rounding=ROUND_HALF_EVEN)


def _refuse_float(value: object) -> object:
    if isinstance(value, float):
        raise ValueError("float refusé : écrire la valeur en Decimal ou en texte")
    return value


_PLAIN_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def _plain_decimal(value: object) -> object:
    """Entier nu, `Decimal` ou décimal en chaîne ; ni flottant, ni « 1e3 »."""
    if isinstance(value, Decimal) or (isinstance(value, int) and not isinstance(value, bool)):
        return value
    if isinstance(value, str) and _PLAIN_DECIMAL.fullmatch(value):
        return value
    raise ValueError("un entier nu ou un décimal en chaîne (« 50.5 ») est attendu")


# Au plus 5 chiffres en écriture décimale, zéros finaux retirés ; les zéros entre
# la virgule et le premier chiffre comptent.
PositiveDecimal = Annotated[Decimal, BeforeValidator(_refuse_float), Field(gt=0, max_digits=5)]

# Valeurs des fichiers de `library/data/` : ni flottant, ni « 1e3 », ni virgule, ni signe.
PlainDecimal = Annotated[Decimal, BeforeValidator(_plain_decimal), Field(gt=0, max_digits=5)]


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
    """Mailles comptées sur une largeur d’échantillon (demi-mailles admises).

    Les rangs et leur hauteur sont facultatifs, mais vont ensemble (CLA-68, ADR 0019).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: PositiveDecimal
    width: Length
    rows: PositiveDecimal | None = None
    height: Length | None = None

    @model_validator(mode="after")
    def _rows_and_height_go_together(self) -> "SwatchMeasurement":
        if (self.rows is None) != (self.height is None):
            raise ValueError("les rangs et leur hauteur vont ensemble : deux valeurs ou aucune")
        return self

    @property
    def stitches_per_10_cm(self) -> Decimal:
        return DIVISION.divide(EXACT.multiply(self.stitches, Decimal(10)), self.width.in_cm)

    @property
    def rows_per_10_cm(self) -> Decimal | None:
        if self.rows is None or self.height is None:
            return None
        return DIVISION.divide(EXACT.multiply(self.rows, Decimal(10)), self.height.in_cm)
