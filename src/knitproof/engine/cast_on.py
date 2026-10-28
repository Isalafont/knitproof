"""Montage : de la largeur visée au nombre de mailles (CLA-65)."""

from decimal import Decimal, localcontext

from knitproof.domain.cast_on import (
    CastOnCheck,
    CastOnRejection,
    CastOnResult,
    RoundingRule,
    StitchMultiple,
)
from knitproof.domain.measure import DIVISION, EXACT, Length, SwatchMeasurement


def stitches_for_width(target: Length, swatch: SwatchMeasurement) -> Decimal:
    """Nombre brut de mailles pour la largeur visée, sans arrondi métier (ADR 0015)."""
    return DIVISION.divide(EXACT.multiply(target.in_cm, swatch.stitches), swatch.width.in_cm)


def cast_on(target: Length, swatch: SwatchMeasurement, stitch: StitchMultiple) -> CastOnResult:
    """Le montage le plus proche du nombre brut qui respecte le point, en dessous si égalité.

    La décision se prend par produits croisés, sans quotient : voisins k-1, k, k+1.
    """
    multiple, offset = stitch.repeat_multiple, stitch.repeat_offset
    with localcontext(EXACT):
        width = swatch.width.in_cm
        wanted = target.in_cm * swatch.stitches
        k = int((wanted - offset * width) // (multiple * width))
        candidates = [n for n in (multiple * j + offset for j in (k - 1, k, k + 1)) if n > 0]
        stitches = min(candidates, key=lambda n: (abs(n * width - wanted), n))
        finished_cm = DIVISION.divide(stitches * width, swatch.stitches)
    return CastOnResult(
        target=target,
        raw_stitches=stitches_for_width(target, swatch),
        stitches=stitches,
        rounding_rule=RoundingRule.NEAREST_TIE_DOWN,
        finished_cm=finished_cm,
    )


def check_cast_on(
    proposed: int, target: Length, swatch: SwatchMeasurement, stitch: StitchMultiple
) -> CastOnCheck:
    """Contrôle un nombre proposé contre le montage calculé ; la largeur finie suit toujours."""
    expected = cast_on(target, swatch, stitch).stitches
    reasons: list[CastOnRejection] = []
    if not stitch.accepts(proposed):
        reasons.append(CastOnRejection.STITCH_MULTIPLE_NOT_RESPECTED)
    if proposed != expected:
        reasons.append(CastOnRejection.DIFFERS_FROM_CALCULATION)
    with localcontext(EXACT):
        proposed_width = proposed * swatch.width.in_cm
    return CastOnCheck(
        proposed=proposed,
        expected=expected,
        reasons=tuple(reasons),
        proposed_finished_cm=DIVISION.divide(proposed_width, swatch.stitches),
    )
