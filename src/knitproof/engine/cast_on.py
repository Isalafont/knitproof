"""Montage : de la largeur visée au nombre de mailles (CLA-65)."""

from decimal import Decimal

from knitproof.domain.measure import DIVISION, EXACT, Length, SwatchMeasurement


def stitches_for_width(target: Length, swatch: SwatchMeasurement) -> Decimal:
    """Nombre brut de mailles pour la largeur visée, sans arrondi métier (ADR 0015)."""
    return DIVISION.divide(EXACT.multiply(target.in_cm, swatch.stitches), swatch.width.in_cm)
