"""La ligne de base « LLM seul » : jauge du cas, verdict et mesure (CLA-188)."""

from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.eval_cases import EvalDataError
from knitproof.domain.measure import SwatchMeasurement
from knitproof.domain.needle import KnittingMethod
from knitproof.engine.gauge import resolve_gauge as resolve_swatch


def resolve_gauge(request: BeanieRequest) -> SwatchMeasurement:
    """La jauge d’un cas, par l’ordre de confiance du moteur ; un cas sans jauge est refusé.

    Un cas à plat est exclu : le montage compte alors 2 lisières (ADR 0028).
    """
    if request.worked is KnittingMethod.FLAT:
        raise EvalDataError("cas à plat exclu de la ligne de base : 2 lisières en plus")
    swatch = request.swatch
    resolved = resolve_swatch(
        blocked=None if swatch is None else swatch.after_blocking,
        unblocked=None if swatch is None else swatch.before_blocking,
        unknown=None if swatch is None else swatch.unknown_blocking,
        label=request.label_gauge,
    )
    if resolved.gauge is None:
        raise EvalDataError("cas sans jauge résolue")
    return resolved.gauge
