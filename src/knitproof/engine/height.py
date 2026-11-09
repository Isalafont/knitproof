"""Rangs d’une hauteur (CLA-68, ADR 0015 et 0028).

L’arrondi se décide par produits croisés, sans quotient ; l’égalité arrondit en dessous,
comme le montage.
"""

from decimal import Decimal, localcontext

from knitproof.domain.beanie import KnittedRows, RowCount, RowRounding
from knitproof.domain.measure import DIVISION, EXACT, Length, SwatchMeasurement


def rounds_for_height(height: Length, swatch: SwatchMeasurement) -> RowCount:
    """Rangs pour une hauteur, avec le nombre brut et la règle d’arrondi."""
    return _rounds_for_cm(height.in_cm, swatch)


def knitted_rows(
    finished: Length, brim: Length, folded: bool, swatch: SwatchMeasurement
) -> KnittedRows:
    """Rangs tricotés au total et au bord ; un revers se tricote deux fois (ADR 0028)."""
    with localcontext(EXACT):
        if folded:
            total_cm = finished.in_cm + brim.in_cm
            brim_cm = brim.in_cm * 2
        else:
            total_cm = finished.in_cm
            brim_cm = brim.in_cm
    return KnittedRows(total=_rounds_for_cm(total_cm, swatch), brim=_rounds_for_cm(brim_cm, swatch))


def _rounds_for_cm(height_cm: Decimal, swatch: SwatchMeasurement) -> RowCount:
    if swatch.rows is None or swatch.height is None:
        raise ValueError("la jauge en rangs est absente de l’échantillon")
    with localcontext(EXACT):
        reference = swatch.height.in_cm
        wanted = height_cm * swatch.rows
        below = int(wanted // reference)
        candidates = [n for n in (below, below + 1) if n > 0]
        rows = min(candidates, key=lambda n: (abs(n * reference - wanted), n))
    return RowCount(
        raw=DIVISION.divide(wanted, reference),
        rows=rows,
        rule=RowRounding.NEAREST_TIE_DOWN,
    )
