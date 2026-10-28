"""Propriétés de la comparaison des aiguilles (CLA-104)."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.needle import (
    Needle,
    NeedleKind,
    NeedleMaterial,
    NeedleMismatch,
    NeedleSize,
    NeedleSystem,
)
from knitproof.engine.needle import check_needles

MMS = st.decimals(
    min_value=Decimal("0.5"), max_value=Decimal("25"), places=2, allow_nan=False
).filter(lambda value: value > 0)
OPTIONAL_MM = st.none() | MMS


@st.composite
def needle_sizes(draw: st.DrawFn) -> NeedleSize:
    system = draw(st.sampled_from(NeedleSystem))
    if system is NeedleSystem.MM:
        value = draw(MMS)
        return NeedleSize(
            system=system, original=f"{value} mm", mm=draw(st.sampled_from([None, value]))
        )
    if system is NeedleSystem.JP:
        number = str(draw(st.integers(min_value=0, max_value=60)))
    elif system is NeedleSystem.US:
        zeros = draw(st.integers(min_value=1, max_value=5))
        number = draw(
            st.sampled_from(
                ["0" * zeros, str(draw(st.integers(1, 40))) + draw(st.sampled_from(["", "½"]))]
            )
        )
    else:
        zeros = draw(st.integers(min_value=1, max_value=5))
        number = draw(st.sampled_from(["0" * zeros, str(draw(st.integers(1, 40)))]))
    return NeedleSize(system=system, original=number, mm=draw(OPTIONAL_MM))


NEEDLES = st.builds(
    Needle,
    size=needle_sizes(),
    kind=st.just(NeedleKind.STRAIGHT),
    material=st.none() | st.sampled_from(NeedleMaterial),
)


def _size_reasons(a: Needle, b: Needle) -> tuple[NeedleMismatch, ...]:
    return tuple(r for r in check_needles(a, b).reasons if r is not NeedleMismatch.MATERIAL_DIFFERS)


@given(a=NEEDLES, b=NEEDLES)
def test_comparison_is_symmetric(a: Needle, b: Needle) -> None:
    assert check_needles(a, b).reasons == check_needles(b, a).reasons


@given(a=NEEDLES)
def test_a_needle_against_itself_has_no_reason(a: Needle) -> None:
    assert check_needles(a, a).reasons == ()


@given(a=NEEDLES, b=NEEDLES)
def test_different_systems_without_both_mm_are_not_comparable(a: Needle, b: Needle) -> None:
    if a.size.system is b.size.system:
        return
    if a.size.known_mm is not None and b.size.known_mm is not None:
        return
    assert _size_reasons(a, b) == (NeedleMismatch.SIZES_NOT_COMPARABLE,)


@given(a=NEEDLES, b=NEEDLES)
def test_equal_known_mm_never_give_a_size_reason(a: Needle, b: Needle) -> None:
    if a.size.known_mm is None or a.size.known_mm != b.size.known_mm:
        return
    assert _size_reasons(a, b) == ()


@given(a=NEEDLES, b=NEEDLES)
def test_material_differs_never_appears_with_an_absent_or_other_material(
    a: Needle, b: Needle
) -> None:
    absent_or_other = {None, NeedleMaterial.OTHER}
    if a.material in absent_or_other or b.material in absent_or_other:
        assert NeedleMismatch.MATERIAL_DIFFERS not in check_needles(a, b).reasons


@given(a=NEEDLES)
def test_no_hidden_conversion_outside_mm(a: Needle) -> None:
    if a.size.system is not NeedleSystem.MM and a.size.mm is None:
        assert a.size.known_mm is None
