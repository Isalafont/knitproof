"""Aiguille circulaire et calotte : rang de passage au magic loop (CLA-68, ADR 0023).

On compare la longueur totale de l’aiguille à la circonférence par produit croisé exact,
sans quotient (ADR 0015). Le câble conseillé vient de `MagicLoopAdvice`, lu par `app`.
"""

from decimal import Decimal, localcontext

from knitproof.domain.construction import MagicLoopAdvice
from knitproof.domain.crown import Crown
from knitproof.domain.measure import EXACT, SwatchMeasurement
from knitproof.domain.needle import Needle, NeedleKind
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.pattern import Pattern
from knitproof.engine.verification import simulate

TO_VERIFY = "À VÉRIFIER : jauge après blocage, le tricot sur l’aiguille peut être plus étroit"


def needle_change(
    crown: Crown,
    needle: Needle,
    after_blocking: SwatchMeasurement,
    before_blocking: SwatchMeasurement | None,
    advice: MagicLoopAdvice,
) -> Notice | None:
    """L’avis sur l’aiguille dans la calotte, ou rien (doubles pointes, aiguille assez courte)."""
    if needle.kind is not NeedleKind.CIRCULAR:
        return None
    options = _options(advice)
    if needle.cable_length is None:
        text = f"À l’entrée de la calotte, passer {options} quand le tricot se tend sur l’aiguille"
        return Notice(
            status=NoticeStatus.WARNING, code=NoticeCode.NEEDLE_CHANGE, text=text, round=1
        )
    gauge = after_blocking if before_blocking is None else before_blocking
    caveat = f" ({TO_VERIFY})" if before_blocking is None else ""
    length = needle.cable_length.in_cm
    if _too_long(length, crown.stitches, gauge):
        text = (
            f"Aiguille de {_plain(length)} cm plus longue que le corps de {crown.stitches} m : "
            f"{options}, ou une circulaire plus courte{caveat}"
        )
        return Notice(status=NoticeStatus.WARNING, code=NoticeCode.NEEDLE_TOO_LONG, text=text)
    for number, count in _round_starts(crown):
        if _too_long(length, count, gauge):
            text = (
                f"Rang {number} de la calotte : {count} m ne tiennent plus sur l’aiguille de "
                f"{_plain(length)} cm, passer {options}{caveat}"
            )
            return Notice(
                status=NoticeStatus.WARNING,
                code=NoticeCode.NEEDLE_CHANGE,
                text=text,
                round=number,
            )
    return None


def _too_long(length: Decimal, stitches: int, gauge: SwatchMeasurement) -> bool:
    """`longueur > circonférence`, soit `longueur * mailles_ech > mailles * largeur_ech`."""
    with localcontext(EXACT):
        return length * gauge.stitches > stitches * gauge.width.in_cm


def _round_starts(crown: Crown) -> list[tuple[int, int]]:
    """Pour chaque rang de la calotte, le compte avec lequel il commence."""
    counts = simulate(Pattern(cast_on=crown.stitches, rounds=crown.rounds)).counts
    starts = [crown.stitches, *(count.stitches for count in counts[:-1])]
    return [(number, start) for number, start in enumerate(starts, start=1)]


def _options(advice: MagicLoopAdvice) -> str:
    cable = advice.magic_loop_cable
    cable_text = f"{_plain(cable.value)} {cable.unit.value}"
    return f"au magic loop (câble de {cable_text} ou plus) ou aux doubles pointes"


def _plain(value: Decimal) -> str:
    return format(value.normalize(), "f")
