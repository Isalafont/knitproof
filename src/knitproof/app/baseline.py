"""La ligne de base « LLM seul » : jauge du cas, verdict et mesure (CLA-188)."""

from decimal import Decimal, localcontext
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.eval_cases import EvalCase, EvalDataError
from knitproof.domain.measure import SwatchMeasurement
from knitproof.domain.needle import KnittingMethod
from knitproof.engine.cast_on import check_cast_on
from knitproof.engine.gauge import resolve_gauge as resolve_swatch

TOLERANCE_CM = Decimal(1)
WILSON_Z = Decimal("1.96")  # 95 %
_WILSON_PRECISION = 28


class CastOnAnswer(BaseModel):
    """Ce que rend le modèle : un nombre de mailles à monter, ou `null` s’il s’abstient."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: int | None


class Verdict(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    ABSTENTION = "abstention"


class Judgement(BaseModel):
    """Le verdict d’une réponse et le tour fini calculé par le moteur (absent sans nombre)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    verdict: Verdict
    finished_cm: Decimal | None


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


def score(case: EvalCase, answer: CastOnAnswer) -> Judgement:
    """Juste si le tour fini du montage rendu tombe à ±1 cm du tour visé, d’après le moteur.

    Un nombre ≤ 0 est faux sans tour fini : le moteur n’accepte que des entiers positifs.
    """
    stitches = answer.stitches
    if stitches is None:
        return Judgement(verdict=Verdict.ABSTENTION, finished_cm=None)
    if stitches <= 0:
        return Judgement(verdict=Verdict.WRONG, finished_cm=None)
    request = case.request
    target = request.circumference
    check = check_cast_on(stitches, target, resolve_gauge(request), request.multiple)
    finished = check.proposed_finished_cm
    close = abs(finished - target.in_cm) <= TOLERANCE_CM
    return Judgement(verdict=Verdict.CORRECT if close else Verdict.WRONG, finished_cm=finished)


def wilson(successes: int, trials: int) -> tuple[Decimal, Decimal]:
    """Intervalle de Wilson à 95 % de `successes` sur `trials`, borné à [0, 1]."""
    if trials < 1:
        raise ValueError("wilson : au moins un essai")
    with localcontext() as context:
        context.prec = _WILSON_PRECISION
        n = Decimal(trials)
        rate = Decimal(successes) / n
        z2 = WILSON_Z * WILSON_Z
        denominator = 1 + z2 / n
        center = (rate + z2 / (2 * n)) / denominator
        half = WILSON_Z * (rate * (1 - rate) / n + z2 / (4 * n * n)).sqrt() / denominator
        low = max(Decimal(0), min(center - half, rate))
        high = min(Decimal(1), max(center + half, rate))
    return low, high
