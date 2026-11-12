"""Lectures de la bibliothèque : tour de tête et hauteurs par âge, fibres par nom (CLA-67)."""

from knitproof.domain.age import Age
from knitproof.domain.fiber import Fiber, name_key
from knitproof.domain.head_size import Sex
from knitproof.domain.needle import NeedleSize, NeedleTableRow
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


def rows_for_age(library: Library, age: Age) -> tuple[ReferenceMeasurement, ...]:
    """Les lignes de la table de hauteurs dont les bornes contiennent l’âge (ADR 0020 §5).

    Un âge peut désigner deux lignes (6 mois, 12 mois, 3 ans) : aucun milieu n’est calculé.
    """
    return tuple(
        found
        for found in _of_quantity(library, Quantity.HEIGHT)
        if found.age is not None and found.age.contains(age)
    )


def needle_rows(library: Library, size: NeedleSize) -> tuple[NeedleTableRow, ...]:
    """Les lignes de la table du système de cette taille ; aucune si elle manque (ADR 0021 §5).

    La comparaison suit `NeedleSize.normalized` : la notation d’origine n’est pas modifiée.
    """
    return tuple(
        row
        for row in library.entries_of(NeedleTableRow)
        if row.system is size.system
        and NeedleSize(system=row.system, original=row.size).normalized == size.normalized
    )


def fiber_named(library: Library, name: str) -> Fiber | None:
    """La fibre que ce nom désigne, NFC et `casefold()` des deux côtés ; l’accent est gardé."""
    key = name_key(name)
    for fiber in library.entries_of(Fiber):
        if any(name_key(known) == key for known in fiber.names):
            return fiber
    return None


def _of_quantity(library: Library, quantity: Quantity) -> tuple[ReferenceMeasurement, ...]:
    return tuple(
        found for found in library.entries_of(ReferenceMeasurement) if found.quantity is quantity
    )
