"""Longueurs et mesure de l’échantillon (CLA-65)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def test_a_length_in_inches_converts_exactly_to_cm() -> None:
    assert Length(value=Decimal("17"), unit=LengthUnit.IN).in_cm == Decimal("43.18")


def test_a_length_in_cm_is_unchanged() -> None:
    assert cm("43.2").in_cm == Decimal("43.2")


@pytest.mark.parametrize("value", ["0", "-1", 22.5, "abc"])
def test_a_length_that_is_not_a_positive_decimal_is_rejected(value: object) -> None:
    with pytest.raises(ValidationError):
        Length.model_validate({"value": value, "unit": "cm"})


def test_a_float_is_refused_with_its_own_message() -> None:
    with pytest.raises(ValidationError, match="float refusé"):
        Length.model_validate({"value": 22.5, "unit": "cm"})


@pytest.mark.parametrize("value", ["99999", "0.00001", "10.0000", "1000.00"])
def test_a_value_of_at_most_five_digits_is_accepted(value: str) -> None:
    # Au plus 5 chiffres en écriture décimale, zéros finaux retirés ; les zéros
    # entre la virgule et le premier chiffre comptent.
    assert Length.model_validate({"value": Decimal(value), "unit": "cm"}).value == Decimal(value)


@pytest.mark.parametrize("value", ["100000", "0.000001", "1000.01"])
def test_a_value_of_more_than_five_digits_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        Length.model_validate({"value": Decimal(value), "unit": "cm"})


def test_a_length_with_more_than_five_digits_is_rejected_not_inexact() -> None:
    with pytest.raises(ValidationError):
        Length.model_validate({"value": Decimal("123456"), "unit": "cm"})


def test_a_length_is_frozen_and_forbids_extra_keys() -> None:
    length = cm("10")

    with pytest.raises(ValidationError):
        length.value = Decimal("11")  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Length.model_validate({"value": "10", "unit": "cm", "extra": 1})


def test_a_swatch_accepts_half_stitches() -> None:
    swatch = SwatchMeasurement(stitches=Decimal("22.5"), width=cm("10"))

    assert swatch.stitches_per_10_cm == Decimal("22.5")


def test_the_gauge_of_22_stitches_over_4_inches() -> None:
    swatch = SwatchMeasurement(
        stitches=Decimal("22"), width=Length(value=Decimal("4"), unit=LengthUnit.IN)
    )

    assert swatch.stitches_per_10_cm == Decimal("21.65354330708661417322834646")


@pytest.mark.parametrize("stitches", ["0", "-5", 22.5])
def test_a_swatch_with_invalid_stitches_is_rejected(stitches: object) -> None:
    with pytest.raises(ValidationError):
        SwatchMeasurement.model_validate(
            {"stitches": stitches, "width": {"value": "10", "unit": "cm"}}
        )


def test_a_swatch_is_frozen_and_forbids_extra_keys() -> None:
    swatch = SwatchMeasurement(stitches=Decimal("20"), width=cm("10"))

    with pytest.raises(ValidationError):
        swatch.stitches = Decimal("21")  # type: ignore[misc]
    with pytest.raises(ValidationError):
        SwatchMeasurement.model_validate(
            {"stitches": "20", "width": {"value": "10", "unit": "cm"}, "rows": "30"}
        )


def test_a_swatch_reads_back_its_own_dump() -> None:
    swatch = SwatchMeasurement(stitches=Decimal("20"), width=cm("10"))

    again = SwatchMeasurement.model_validate(swatch.model_dump())

    assert again == swatch
    assert again.stitches_per_10_cm == Decimal("20")


def test_a_swatch_reads_back_its_own_json_dump() -> None:
    swatch = SwatchMeasurement(
        stitches=Decimal("22.5"), width=Length(value=Decimal("4"), unit=LengthUnit.IN)
    )

    assert SwatchMeasurement.model_validate(swatch.model_dump(mode="json")) == swatch
