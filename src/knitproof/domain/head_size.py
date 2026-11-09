"""Tailles nommées du tour de tête et sexe adulte (CLA-112, ADR 0026).

Aucune plage ici : la grille se charge avec CLA-118, la résolution vient avec CLA-119.
"""

from enum import StrEnum


class HeadSize(StrEnum):
    MONTHS_0_3 = "months_0_3"
    MONTHS_6 = "months_6"
    MONTHS_9 = "months_9"
    MONTHS_12 = "months_12"
    MONTHS_18 = "months_18"
    MONTHS_24 = "months_24"
    YEARS_2_3 = "years_2_3"
    YEARS_4 = "years_4"
    YEARS_5_7 = "years_5_7"
    YEARS_7_9 = "years_7_9"
    YEARS_10_12 = "years_10_12"
    YEARS_12_14 = "years_12_14"
    YEARS_14_16 = "years_14_16"
    YEARS_17 = "years_17"
    ADULT_S = "adult_s"
    ADULT_M = "adult_m"
    ADULT_L = "adult_l"

    @property
    def is_adult(self) -> bool:
        return self in {HeadSize.ADULT_S, HeadSize.ADULT_M, HeadSize.ADULT_L}


class Sex(StrEnum):
    """Le sexe n’entre que pour les tailles adultes, là où la grille sépare femme et homme."""

    FEMALE = "female"
    MALE = "male"
