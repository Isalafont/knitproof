"""Âge de la spécification, en mois avant 2 ans et en années ensuite (CLA-112, ADR 0018 §8)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.age import Age, AgeUnit


def test_three_years_is_thirty_six_months() -> None:
    assert Age(value=3, unit=AgeUnit.YEARS).in_months == 36


@pytest.mark.parametrize("value", [0, 1, 23])
def test_months_below_two_years_are_accepted(value: int) -> None:
    age = Age(value=value, unit=AgeUnit.MONTHS)

    assert age.in_months == value
    assert age.unit is AgeUnit.MONTHS


def test_two_years_is_accepted_and_keeps_its_unit() -> None:
    age = Age(value=2, unit=AgeUnit.YEARS)

    assert age.in_months == 24
    assert age.unit is AgeUnit.YEARS


def test_one_year_is_refused_because_it_is_written_in_months() -> None:
    with pytest.raises(ValidationError, match="en mois avant 2 ans"):
        Age(value=1, unit=AgeUnit.YEARS)


def test_twenty_four_months_is_refused_because_it_is_written_in_years() -> None:
    with pytest.raises(ValidationError, match="en années à partir de 2 ans"):
        Age(value=24, unit=AgeUnit.MONTHS)


def test_a_negative_age_is_refused() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        Age(value=-1, unit=AgeUnit.MONTHS)


@pytest.mark.parametrize("value", [3.0, "3", True])
def test_a_value_that_is_not_an_integer_is_refused(value: object) -> None:
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        Age.model_validate({"value": value, "unit": "years"})


def test_an_unknown_unit_is_refused() -> None:
    with pytest.raises(ValidationError, match="months"):
        Age.model_validate({"value": 3, "unit": "weeks"})


def test_an_extra_field_is_refused() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        Age.model_validate({"value": 3, "unit": "years", "days": 1})
