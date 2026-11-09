"""Aisance saisie, en % ou en cm, unité d’origine gardée (CLA-112, ADR 0024 §2)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.ease import Ease, EaseUnit


def test_a_negative_percentage_keeps_its_value_and_unit() -> None:
    ease = Ease(value=Decimal("-15.6"), unit=EaseUnit.PERCENT)

    assert ease.value == Decimal("-15.6")
    assert ease.unit is EaseUnit.PERCENT


def test_centimetres_keep_their_unit() -> None:
    ease = Ease(value=Decimal(2), unit=EaseUnit.CM)

    assert ease.unit is EaseUnit.CM


def test_zero_is_accepted() -> None:
    assert Ease(value=Decimal(0), unit=EaseUnit.PERCENT).value == 0


def test_a_float_is_refused() -> None:
    with pytest.raises(ValidationError, match="float refusé"):
        Ease.model_validate({"value": -15.6, "unit": "percent"})


def test_more_than_five_digits_are_refused() -> None:
    with pytest.raises(ValidationError, match="no more than 5 digits"):
        Ease(value=Decimal("-1234.56"), unit=EaseUnit.CM)


def test_the_sign_does_not_count_as_a_digit() -> None:
    assert Ease(value=Decimal("-12345"), unit=EaseUnit.CM).value == Decimal(-12345)


def test_an_unknown_unit_is_refused() -> None:
    with pytest.raises(ValidationError, match="percent"):
        Ease.model_validate({"value": "2", "unit": "in"})
