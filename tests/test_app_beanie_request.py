"""`BeanieRequest` : la demande de bonnet en YAML (CLA-69, CLA-104)."""

from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.errors import condense
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.measure import EXACT, Length, LengthUnit
from knitproof.domain.needle import KnittingMethod, NeedleKind, NeedleSize, NeedleSystem

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "bonnet-3-ans.yaml"


def _data() -> dict[str, object]:
    loaded = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _with_needle(size: object) -> dict[str, object]:
    return {**_data(), "needles": [{"size": size, "kind": "double_pointed"}]}


def test_the_example_gives_the_specification() -> None:
    request = BeanieRequest.model_validate(_data())

    spec = request.specification

    assert spec.total_height == Length(value=Decimal(20), unit=LengthUnit.CM)
    assert spec.brim_height == Length(value=Decimal(5), unit=LengthUnit.CM)
    assert spec.folded_brim
    assert spec.worked is KnittingMethod.ROUND
    assert [needle.kind for needle in spec.needles] == [NeedleKind.DOUBLE_POINTED]
    assert spec.needles[0].size == NeedleSize(system=NeedleSystem.MM, original="4")


def test_the_target_circumference_applies_the_ease() -> None:
    request = BeanieRequest.model_validate(_data())

    assert request.circumference == Length(value=Decimal("43.2"), unit=LengthUnit.CM)
    assert EXACT.multiply(Decimal(48), Decimal(90)) / 100 == Decimal("43.2")


def test_a_centimetre_ease_is_added_to_the_head() -> None:
    data = {**_data(), "ease": {"value": "-4", "unit": "cm", "provenance": "entered"}}

    assert BeanieRequest.model_validate(data).circumference.in_cm == Decimal(44)


def test_the_example_gives_the_multiple_swatches_and_the_proposed_cast_on() -> None:
    request = BeanieRequest.model_validate(_data())

    assert request.multiple == StitchMultiple(repeat_multiple=4, repeat_offset=0)
    assert request.swatch.after_blocking.stitches == Decimal(20)
    assert request.swatch.before_blocking is not None
    assert request.swatch.before_blocking.stitches == Decimal(22)
    assert request.proposed_cast_on is not None
    assert request.proposed_cast_on.stitches == 120


def test_a_us_needle_with_its_mm_is_split_at_the_door() -> None:
    request = BeanieRequest.model_validate(_with_needle("US 6 (4 mm)"))

    assert request.specification.needles[0].size == NeedleSize(
        system=NeedleSystem.US, original="6", mm=Decimal(4)
    )


def test_a_us_needle_without_mm_and_a_mm_needle() -> None:
    us = BeanieRequest.model_validate(_with_needle("US 99")).specification.needles[0].size
    mm = BeanieRequest.model_validate(_with_needle("4,25 mm")).specification.needles[0].size

    assert (us.system, us.original, us.mm) == (NeedleSystem.US, "99", None)
    assert (mm.system, mm.original) == (NeedleSystem.MM, "4,25")


@pytest.mark.parametrize("size", ["gros", "US", "US 6 (4 mm", "6 (4 mm)", "", "US 6 (x mm)"])
def test_an_unknown_needle_form_is_refused_with_a_clear_message(size: str) -> None:
    with pytest.raises(ValidationError) as raised:
        BeanieRequest.model_validate(_with_needle(size))

    message = condense(raised.value, _with_needle(size))
    assert "taille d’aiguille" in message
    assert "« 4 mm »" in message
    assert "Value error" not in message


def test_an_extra_key_is_refused() -> None:
    with pytest.raises(ValidationError) as raised:
        BeanieRequest.model_validate({**_data(), "garment": "beanie"})

    assert [error["type"] for error in raised.value.errors()] == ["extra_forbidden"]


def test_a_brim_higher_than_the_height_is_refused_at_validation() -> None:
    data = {**_data(), "brim_height": {"value": "25", "unit": "cm", "provenance": "entered"}}

    with pytest.raises(ValidationError, match="le bord doit être plus bas"):
        BeanieRequest.model_validate(data)


def test_a_computation_error_is_in_french() -> None:
    data = {**_data(), "ease": {"value": "-100", "unit": "percent", "provenance": "entered"}}

    with pytest.raises(ValidationError) as raised:
        BeanieRequest.model_validate(data)

    assert "Input should be" not in str(raised.value)
    assert "supérieur à 0" in str(raised.value)


def test_the_row_gauge_accepts_a_source() -> None:
    data = _data()
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    swatch["after_blocking"] = {
        **swatch["after_blocking"],
        "rows_source": {"reference": "DROPS Children 49-25", "to_verify": True},
    }

    source = BeanieRequest.model_validate(data).swatch.after_blocking.rows_source

    assert source is not None
    assert (source.reference, source.to_verify) == ("DROPS Children 49-25", True)


def test_the_row_gauge_source_is_optional() -> None:
    data = _data()
    swatch = data["swatch"]
    assert isinstance(swatch, dict)
    swatch["after_blocking"] = {
        key: value for key, value in swatch["after_blocking"].items() if key != "rows_source"
    }

    assert BeanieRequest.model_validate(data).swatch.after_blocking.rows_source is None
