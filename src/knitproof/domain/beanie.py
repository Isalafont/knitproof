"""Spécification d’un bonnet : l’entrée typée d’une demande (CLA-112, ADR 0003).

Rien n’est résolu ici : une spécification peut ne contenir que des aiguilles, la question
vient de la résolution (tour de tête, hauteurs, aisance).
"""

from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from knitproof.domain.age import Age
from knitproof.domain.ease import Ease
from knitproof.domain.head_size import HeadSize, Sex
from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.measure import Length
from knitproof.domain.needle import KnittingMethod, Needle, NeedleKind


class RowRounding(StrEnum):
    NEAREST_TIE_DOWN = "nearest_tie_down"


class RowCount(BaseModel):
    """Rangs d’une hauteur, avec la trace de l’arrondi (ADR 0028)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    raw: Decimal
    rows: StrictPositiveInt
    rule: RowRounding


class KnittedRows(BaseModel):
    """Rangs tricotés au total et rangs du bord, tous deux arrondis une fois."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total: RowCount
    brim: RowCount


ROUND_KINDS = frozenset({NeedleKind.CIRCULAR, NeedleKind.DOUBLE_POINTED})


class BeanieSpecification(BaseModel):
    """Ce que demande la personne, unités d’origine gardées.

    `size`, `age` et `head` peuvent coexister (ADR 0020, ADR 0026 §11) ; `sex` n’entre que
    pour une taille adulte (ADR 0026 §9). `brim_height` est la hauteur visible du revers si
    `folded_brim`, sinon celle du bord ; `total_height` est la hauteur finie (ADR 0020).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    age: Age | None = None
    head: Length | None = None
    size: HeadSize | None = None
    sex: Sex | None = None
    yarn_id: str | None = None
    body_swatch_id: str | None = None
    brim_swatch_id: str | None = None
    brim_pattern_id: str | None = None
    body_pattern_id: str | None = None
    ease: Ease | None = None
    brim_height: Length | None = None
    folded_brim: bool = False
    total_height: Length | None = None
    worked: KnittingMethod = KnittingMethod.ROUND
    needles: tuple[Needle, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _is_consistent(self) -> Self:
        self._check_sex()
        self._check_heights()
        self._check_needles_allow_the_method()
        return self

    def _check_sex(self) -> None:
        if self.sex is not None and (self.size is None or not self.size.is_adult):
            raise ValueError("le sexe n’entre que pour une taille adulte (ADR 0026 §9)")

    def _check_heights(self) -> None:
        if self.brim_height is None or self.total_height is None:
            return
        if self.brim_height.in_cm >= self.total_height.in_cm:
            raise ValueError("le bord doit être plus bas que la hauteur totale")

    def _check_needles_allow_the_method(self) -> None:
        if self.worked is KnittingMethod.ROUND and not any(
            needle.kind in ROUND_KINDS for needle in self.needles
        ):
            raise ValueError("tricoter en rond demande une aiguille circulaire ou à double pointe")
