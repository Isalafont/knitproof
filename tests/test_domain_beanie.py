"""Spécification d’un bonnet (CLA-112, ADR 0003, 0018 à 0020, 0026)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.age import Age, AgeUnit
from knitproof.domain.beanie import BeanieSpecification
from knitproof.domain.ease import Ease, EaseUnit
from knitproof.domain.head_size import HeadSize, Sex
from knitproof.domain.measure import Length, LengthUnit
from knitproof.domain.needle import KnittingMethod, Needle, NeedleKind, NeedleSize, NeedleSystem


def needle(kind: NeedleKind) -> Needle:
    return Needle(size=NeedleSize(system=NeedleSystem.MM, original="3.5"), kind=kind)


CIRCULAR = needle(NeedleKind.CIRCULAR)
DOUBLE_POINTED = needle(NeedleKind.DOUBLE_POINTED)
STRAIGHT = needle(NeedleKind.STRAIGHT)


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def inches(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.IN)


def test_a_complete_specification_keeps_the_original_units() -> None:
    spec = BeanieSpecification(
        age=Age(value=3, unit=AgeUnit.YEARS),
        head=inches("20"),
        yarn_id="drops-alpaca",
        body_swatch_id="body",
        brim_swatch_id="brim",
        brim_pattern_id="rib-2x2",
        body_pattern_id="stockinette",
        ease=Ease(value=Decimal("-10"), unit=EaseUnit.PERCENT),
        brim_height=inches("2"),
        folded_brim=True,
        total_height=cm("20"),
        worked=KnittingMethod.ROUND,
        needles=(CIRCULAR, DOUBLE_POINTED),
    )

    assert spec.head == inches("20")
    assert spec.brim_height == inches("2")
    assert spec.age is not None
    assert spec.age.in_months == 36
    assert spec.ease is not None
    assert spec.ease.unit is EaseUnit.PERCENT
    assert spec.needles == (CIRCULAR, DOUBLE_POINTED)


def test_a_specification_with_only_needles_is_accepted() -> None:
    spec = BeanieSpecification(needles=(CIRCULAR,))

    assert spec.worked is KnittingMethod.ROUND
    assert spec.folded_brim is False
    assert spec.age is None
    assert spec.head is None
    assert spec.size is None
    assert spec.sex is None
    assert spec.ease is None
    assert spec.brim_height is None
    assert spec.total_height is None


def test_a_list_of_needles_becomes_a_tuple() -> None:
    spec = BeanieSpecification.model_validate({"needles": [CIRCULAR]})

    assert spec.needles == (CIRCULAR,)


def test_the_specification_is_frozen_and_hashable() -> None:
    spec = BeanieSpecification(needles=(CIRCULAR,))

    assert hash(spec) == hash(BeanieSpecification(needles=(CIRCULAR,)))
    with pytest.raises(ValidationError, match="frozen"):
        spec.folded_brim = True  # type: ignore[misc]


def test_size_age_and_head_may_coexist() -> None:
    spec = BeanieSpecification(
        age=Age(value=3, unit=AgeUnit.YEARS),
        size=HeadSize.YEARS_2_3,
        head=cm("50"),
        needles=(CIRCULAR,),
    )

    assert spec.size is HeadSize.YEARS_2_3
    assert spec.head == cm("50")


@pytest.mark.parametrize("size", [HeadSize.ADULT_S, HeadSize.ADULT_M, HeadSize.ADULT_L])
def test_a_sex_with_an_adult_size_is_accepted(size: HeadSize) -> None:
    spec = BeanieSpecification(size=size, sex=Sex.FEMALE, needles=(CIRCULAR,))

    assert spec.sex is Sex.FEMALE


def test_a_sex_without_a_size_is_refused() -> None:
    with pytest.raises(ValidationError, match="sexe n’entre que pour une taille adulte"):
        BeanieSpecification(sex=Sex.MALE, needles=(CIRCULAR,))


def test_a_sex_with_a_size_below_adult_is_refused() -> None:
    with pytest.raises(ValidationError, match="sexe n’entre que pour une taille adulte"):
        BeanieSpecification(size=HeadSize.MONTHS_0_3, sex=Sex.MALE, needles=(CIRCULAR,))


def test_a_brim_taller_than_the_total_height_is_refused() -> None:
    with pytest.raises(ValidationError, match="bord doit être plus bas que la hauteur totale"):
        BeanieSpecification(brim_height=cm("21"), total_height=cm("20"), needles=(CIRCULAR,))


def test_a_brim_as_tall_as_the_total_height_is_refused() -> None:
    with pytest.raises(ValidationError, match="bord doit être plus bas que la hauteur totale"):
        BeanieSpecification(brim_height=cm("20"), total_height=cm("20"), needles=(CIRCULAR,))


def test_heights_in_different_units_are_compared_in_centimetres() -> None:
    with pytest.raises(ValidationError, match="bord doit être plus bas que la hauteur totale"):
        BeanieSpecification(brim_height=cm("26"), total_height=inches("10"), needles=(CIRCULAR,))


def test_a_brim_in_inches_taller_than_a_total_height_in_centimetres_is_refused() -> None:
    with pytest.raises(ValidationError, match="bord doit être plus bas que la hauteur totale"):
        BeanieSpecification(brim_height=inches("2"), total_height=cm("5"), needles=(CIRCULAR,))


def test_a_brim_in_centimetres_lower_than_a_total_height_in_inches_is_accepted() -> None:
    spec = BeanieSpecification(brim_height=cm("15"), total_height=inches("10"), needles=(CIRCULAR,))

    assert spec.brim_height == cm("15")


def test_a_brim_lower_than_the_total_height_is_accepted_across_units() -> None:
    spec = BeanieSpecification(brim_height=cm("5"), total_height=inches("10"), needles=(CIRCULAR,))

    assert spec.total_height == inches("10")


def test_a_brim_without_a_total_height_is_accepted() -> None:
    assert BeanieSpecification(brim_height=cm("5"), needles=(CIRCULAR,)).brim_height == cm("5")


def test_no_needle_is_refused() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        BeanieSpecification(needles=())


def test_straight_needles_alone_are_refused_for_round_knitting() -> None:
    with pytest.raises(ValidationError, match="circulaire ou à double pointe"):
        BeanieSpecification(needles=(STRAIGHT,), worked=KnittingMethod.ROUND)


def test_straight_needles_alone_are_refused_by_default() -> None:
    with pytest.raises(ValidationError, match="circulaire ou à double pointe"):
        BeanieSpecification(needles=(STRAIGHT,))


def test_straight_needles_are_accepted_for_flat_knitting() -> None:
    spec = BeanieSpecification(needles=(STRAIGHT,), worked=KnittingMethod.FLAT)

    assert spec.worked is KnittingMethod.FLAT


@pytest.mark.parametrize("needles", [(STRAIGHT, CIRCULAR), (STRAIGHT, DOUBLE_POINTED)])
def test_one_suitable_needle_is_enough_for_round_knitting(needles: tuple[Needle, ...]) -> None:
    assert BeanieSpecification(needles=needles).needles == needles


def test_crown_sectors_is_refused() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        BeanieSpecification.model_validate({"needles": [CIRCULAR], "crown_sectors": 4})


def test_an_unknown_method_is_refused() -> None:
    with pytest.raises(ValidationError, match="flat"):
        BeanieSpecification.model_validate({"needles": [CIRCULAR], "worked": "crochet"})
