"""Comparaison des aiguilles de l’échantillon et du projet (CLA-104, ADR 0016)."""

from knitproof.domain.needle import Needle, NeedleCheck, NeedleMaterial, NeedleMismatch


def check_needles(swatch: Needle, project: Needle) -> NeedleCheck:
    """`swatch_needle_mismatch` : deux systèmes ne se comparent qu’avec un `mm` saisi."""
    found = (_size_mismatch(swatch, project), _material_mismatch(swatch, project))
    reasons = [r for r in found if r is not None]
    return NeedleCheck(swatch=swatch, project=project, reasons=tuple(reasons))


def _size_mismatch(a: Needle, b: Needle) -> NeedleMismatch | None:
    mm_a, mm_b = a.size.known_mm, b.size.known_mm
    if mm_a is not None and mm_b is not None:
        return None if mm_a == mm_b else NeedleMismatch.SIZE_DIFFERS
    if a.size.system is not b.size.system:
        return NeedleMismatch.SIZES_NOT_COMPARABLE
    return None if a.size.normalized == b.size.normalized else NeedleMismatch.SIZE_DIFFERS


def _material_mismatch(a: Needle, b: Needle) -> NeedleMismatch | None:
    if a.material is None or b.material is None:
        return None
    if NeedleMaterial.OTHER in (a.material, b.material):
        return None
    return NeedleMismatch.MATERIAL_DIFFERS if a.material is not b.material else None
