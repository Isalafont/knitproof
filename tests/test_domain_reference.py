"""Mesures de référence : bornes d’âge, plages, hauteurs (CLA-67)."""

import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.age import Age, AgeUnit
from knitproof.domain.head_size import Sex
from knitproof.domain.measure import LengthUnit
from knitproof.domain.reference import (
    AgeBounds,
    LengthRange,
    Quantity,
    ReferenceLength,
    ReferenceMeasurement,
)

SOURCE = {"kind": "reference_measurement", "reference": "x", "read_on": datetime.date(2026, 11, 9)}


def months(value: int) -> Age:
    return Age(value=value, unit=AgeUnit.MONTHS)


def test_age_bounds_include_both_ends() -> None:
    bounds = AgeBounds(min_months=3, max_months=6)

    assert [bounds.contains(months(m)) for m in (2, 3, 5, 6, 7)] == [False, True, True, True, False]


def test_an_age_in_years_is_compared_in_months() -> None:
    bounds = AgeBounds(min_months=36, max_months=48)

    assert bounds.contains(Age(value=3, unit=AgeUnit.YEARS))
    assert bounds.contains(Age(value=4, unit=AgeUnit.YEARS))
    assert not bounds.contains(Age(value=5, unit=AgeUnit.YEARS))


def test_open_ended_bounds_have_no_upper_limit() -> None:
    bounds = AgeBounds(min_months=180)

    assert bounds.contains(Age(value=90, unit=AgeUnit.YEARS))
    assert not bounds.contains(Age(value=14, unit=AgeUnit.YEARS))


def test_age_bounds_refuse_an_upper_bound_below_the_lower() -> None:
    with pytest.raises(ValidationError, match="max_months"):
        AgeBounds(min_months=6, max_months=3)


def test_a_range_keeps_its_unit_and_converts_on_demand() -> None:
    span = LengthRange(low=Decimal(20), high=Decimal("23.75"), unit=LengthUnit.IN)

    assert span.high_length.value == Decimal("23.75")
    assert span.high_length.unit is LengthUnit.IN
    assert span.low_length is not None
    assert span.low_length.in_cm == Decimal("50.80")


def test_a_range_may_have_only_an_upper_bound() -> None:
    span = LengthRange(high=Decimal(35), unit=LengthUnit.CM)

    assert span.low is None
    assert span.low_length is None


def test_a_range_refuses_a_low_above_the_high() -> None:
    with pytest.raises(ValidationError, match="low"):
        LengthRange(low=Decimal(40), high=Decimal(35), unit=LengthUnit.CM)


def test_a_head_measurement_needs_a_range() -> None:
    with pytest.raises(ValidationError, match="span"):
        ReferenceMeasurement.model_validate(
            {"id": "a", "quantity": "head_circumference", "source": SOURCE}
        )


def test_a_height_measurement_needs_a_value() -> None:
    with pytest.raises(ValidationError, match="value"):
        ReferenceMeasurement.model_validate({"id": "a", "quantity": "height", "source": SOURCE})


def test_a_head_measurement_refuses_a_single_value() -> None:
    with pytest.raises(ValidationError, match="value"):
        ReferenceMeasurement.model_validate(
            {
                "id": "a",
                "quantity": "head_circumference",
                "span": {"high": "35", "unit": "cm"},
                "value": {"value": "8", "unit": "in"},
                "source": SOURCE,
            }
        )


def test_a_reference_length_keeps_its_unit() -> None:
    value = ReferenceLength(value=Decimal("3.5"), unit=LengthUnit.IN)

    assert value.length.value == Decimal("3.5")
    assert value.length.unit is LengthUnit.IN


def test_a_measurement_never_carries_a_proposed_value() -> None:
    assert "proposed" not in "".join(ReferenceMeasurement.model_fields)
    assert Quantity.HEAD_CIRCUMFERENCE.value == "head_circumference"
    assert Sex.FEMALE.value == "female"
