"""Aisance de référence : le % se déduit des données brutes de la source (CLA-67, ADR 0024 §7)."""

from collections.abc import Sequence
from decimal import Decimal

from knitproof.domain.ease import (
    BaseEase,
    EaseOrigin,
    EaseOutcome,
    EaseProposal,
    EaseRole,
    EaseSize,
    EaseSource,
    EdgeStitch,
    Fit,
)
from knitproof.domain.measure import DIVISION, EXACT
from knitproof.domain.yarn import Yarn, YarnFamily

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


def propose_ease(
    sources: Sequence[EaseSource],
    yarns: Sequence[Yarn],
    bases: Sequence[BaseEase],
    fit: Fit,
    edge: EdgeStitch,
    swatch_stitch: EdgeStitch,
    yarn_id: str | None,
) -> EaseOutcome:
    """Valeur d’après les patrons qui correspondent, sinon la base, sinon aucune (ADR 0031).

    Un patron `proposal` compte s’il a le même ajustement et le même bord, si son échantillon est
    au même point (ou absent) et si sa laine est de la famille de celle demandée (ou absente).
    Plusieurs patrons : médiane de leurs médianes. Les autres sources du couple sont des repères.
    """
    same_edge = [item for item in sources if (item.fit, item.edge) == (fit, edge)]
    counted = [
        item
        for item in same_edge
        if item.role is EaseRole.PROPOSAL
        and _same_swatch_stitch(item, swatch_stitch)
        and _fits_the_yarn(item, yarns, yarn_id)
    ]
    landmarks = tuple(reference_ease(item) for item in same_edge if item not in counted)
    if counted:
        return _from_patterns(tuple(reference_ease(item) for item in counted), landmarks)
    for base in bases:
        if (base.fit, base.swatch_stitch) == (fit, swatch_stitch) and edge in base.edges:
            return EaseOutcome(
                origin=EaseOrigin.BASE,
                value=base.value,
                low=base.value,
                high=base.value,
                base=base,
                landmarks=landmarks,
            )
    return EaseOutcome(origin=EaseOrigin.NONE, landmarks=landmarks)


def _from_patterns(
    proposals: tuple[EaseProposal, ...], landmarks: tuple[EaseProposal, ...]
) -> EaseOutcome:
    medians = tuple(item.proposed for item in proposals)
    every_size = tuple(value for item in proposals for value in item.by_size)
    if len(proposals) == 1:
        [only] = proposals
        low, high = only.low, only.high
    else:
        low, high = min(medians), max(medians)
    return EaseOutcome(
        origin=EaseOrigin.SOURCES,
        value=min(max(_median(medians), low), high),
        low=low,
        high=high,
        size_low=min(every_size),
        size_high=max(every_size),
        sources=proposals,
        landmarks=landmarks,
    )


def _same_swatch_stitch(source: EaseSource, swatch_stitch: EdgeStitch) -> bool:
    return source.swatch is None or source.swatch.stitch is swatch_stitch


def _fits_the_yarn(source: EaseSource, yarns: Sequence[Yarn], yarn_id: str | None) -> bool:
    if not source.yarns:
        return True
    if yarn_id is None:
        return False
    if yarn_id in source.yarns:
        return True
    wanted = _family_of(yarns, yarn_id)
    if wanted is None:
        return False
    return any(_family_of(yarns, cited) == wanted for cited in source.yarns)


def _family_of(yarns: Sequence[Yarn], yarn_id: str) -> YarnFamily | None:
    return next((item.family for item in yarns if item.id == yarn_id), None)


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
