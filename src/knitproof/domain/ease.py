"""Aisance saisie, en % ou en cm (CLA-112, ADR 0024 §2)."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from knitproof.domain.measure import _refuse_float

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
