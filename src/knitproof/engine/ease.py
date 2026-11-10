"""Aisance de référence : le % se déduit des données brutes de la source (CLA-67, ADR 0024 §7)."""

from decimal import Decimal

from knitproof.domain.ease import EaseProposal, EaseSize, EaseSource
from knitproof.domain.measure import DIVISION, EXACT

HUNDRED = Decimal(100)
TEN = Decimal(10)
TWO = Decimal(2)


def reference_ease(source: EaseSource) -> EaseProposal:
    """Aisance au milieu de la plage de tête de chaque taille, puis valeur proposée et plage.

    Plusieurs tailles : médiane des tailles, plage du plus faible au plus fort. Une taille :
    valeur au milieu de sa plage de tête, plage aux deux bornes de la tête (lecture de
    l’ADR 0024 pour le Rosebud, à confirmer).
    """
    by_size = tuple(_ease_at(source, size, _head_middle(size)) for size in source.sizes)
    if len(source.sizes) == 1:
        [size] = source.sizes
        ends = [_ease_at(source, size, head) for head in _head_ends(size)]
        low, high = min(ends), max(ends)
    else:
        low, high = min(by_size), max(by_size)
    return EaseProposal(
        source_id=source.id,
        fit=source.fit,
        edge=source.edge,
        proposed=min(
            max(_median(by_size), low), high
        ),  # l’arrondi à 28 chiffres reste dans la plage
        low=low,
        high=high,
        by_size=by_size,
        provenance=source.source,
    )


def _ease_at(source: EaseSource, size: EaseSize, head_cm: Decimal) -> Decimal:
    gap = DIVISION.subtract(_circumference_cm(source, size), head_cm)
    return DIVISION.divide(DIVISION.multiply(gap, HUNDRED), head_cm)


def _circumference_cm(source: EaseSource, size: EaseSize) -> Decimal:
    if size.brim_circumference is not None:
        return size.brim_circumference.length.in_cm
    # Une taille porte cast_on ou brim_circumference, et un montage exige l’échantillon (domain).
    assert size.cast_on is not None
    assert source.swatch is not None
    per_10_cm = source.swatch.measurement.stitches_per_10_cm
    return DIVISION.divide(EXACT.multiply(Decimal(size.cast_on), TEN), per_10_cm)


def _head_ends(size: EaseSize) -> tuple[Decimal, Decimal]:
    low = size.head.low_length
    assert low is not None
    return low.in_cm, size.head.high_length.in_cm


def _head_middle(size: EaseSize) -> Decimal:
    low, high = _head_ends(size)
    return DIVISION.divide(DIVISION.add(low, high), TWO)


def _median(values: tuple[Decimal, ...]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return DIVISION.divide(DIVISION.add(ordered[middle - 1], ordered[middle]), TWO)
