"""Lectures de la bibliothèque : tour de tête par âge, hauteurs par âge (CLA-67)."""

from knitproof.domain.age import Age
from knitproof.domain.head_size import Sex
from knitproof.domain.reference import Quantity, ReferenceMeasurement
from knitproof.library.loader import Library


def head_ranges_for(
    library: Library, age: Age, sex: Sex | None = None
) -> tuple[ReferenceMeasurement, ...]:
    """Les plages de tour de tête dont les bornes contiennent l’âge (ADR 0027).

    Avec un sexe, seules les plages sans sexe ou de ce sexe ; sans sexe, toutes celles de l’âge.
    """
    return tuple(
        found
        for found in _of_quantity(library, Quantity.HEAD_CIRCUMFERENCE)
        if found.age is not None
        and found.age.contains(age)
        and (sex is None or found.sex in (None, sex))
    )


def _of_quantity(library: Library, quantity: Quantity) -> tuple[ReferenceMeasurement, ...]:
    return tuple(
        found for found in library.entries_of(ReferenceMeasurement) if found.quantity is quantity
    )
