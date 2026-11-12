"""Le vocabulaire des fibres et la composition d’un fil (CLA-121, ADR 0030)."""

import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.fiber import Fiber, FiberComposition, FiberShare, name_key

SOURCE = {
    "kind": "person_decision",
    "reference": "Isabelle Lafont, décision du 12/11/2026 (CLA-121)",
    "read_on": datetime.date(2026, 11, 12),
}


def fiber(names: list[str]) -> dict[str, object]:
    return {"id": "alpaca", "names": names, "source": SOURCE}


def share(fiber_id: str, percent: object, term: str = "x") -> dict[str, object]:
    return {"fiber": fiber_id, "label_term": term, "percent": percent}


def test_a_fiber_with_names_is_accepted() -> None:
    assert Fiber.model_validate(fiber(["alpaga", "alpaca"])).names == ("alpaga", "alpaca")


def test_a_fiber_needs_a_name() -> None:
    with pytest.raises(ValidationError):
        Fiber.model_validate(fiber([]))


def test_a_blank_name_is_refused() -> None:
    with pytest.raises(ValidationError):
        Fiber.model_validate(fiber(["alpaga", " "]))


@pytest.mark.parametrize("names", [["a", "A"], ["Mérinos", "mérinos"]])
def test_names_of_a_fiber_are_unique_by_key(names: list[str]) -> None:
    with pytest.raises(ValidationError, match="nom en double"):
        Fiber.model_validate(fiber(names))


def test_a_fiber_refuses_an_unknown_key() -> None:
    with pytest.raises(ValidationError):
        Fiber.model_validate({**fiber(["alpaca"]), "blocking_change": "1"})


def test_the_name_key_ignores_case_and_unicode_form() -> None:
    assert name_key("Mérinos") == name_key("Mérinos".lower())
    assert name_key("merinos") != name_key("mérinos")


def test_a_blend_of_strings_is_accepted() -> None:
    composition = FiberComposition.model_validate(
        {"parts": [share("merino", "80", "uld"), share("nylon", "20", "nylon")]}
    )
    assert composition.parts[0].percent == Decimal(80)
    assert composition.parts[1].label_term == "nylon"


def test_bare_integers_are_accepted() -> None:
    parts = [share("alpaca", 65), share("polyamide", 28), share("wool", 7)]
    assert len(FiberComposition.model_validate({"parts": parts}).parts) == 3


def test_exact_decimals_sum_to_100() -> None:
    parts = [share("a", "33.3"), share("b", "66.7")]
    assert FiberComposition.model_validate({"parts": parts}).parts[0].percent == Decimal("33.3")


def test_a_single_fiber_at_100_is_accepted() -> None:
    assert FiberComposition.model_validate({"parts": [share("wool", 100)]})


def test_a_sum_other_than_100_is_refused() -> None:
    with pytest.raises(ValidationError, match="somme"):
        FiberComposition.model_validate({"parts": [share("a", 65), share("b", 34)]})


def test_a_fiber_twice_is_refused() -> None:
    with pytest.raises(ValidationError, match="fibre en double"):
        FiberComposition.model_validate({"parts": [share("a", 50), share("a", 50)]})


def test_a_part_above_100_is_refused() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 100"):
        FiberShare.model_validate(share("a", 101))


def test_a_float_percent_is_refused() -> None:
    with pytest.raises(ValidationError):
        FiberComposition.model_validate({"parts": [share("a", 100.0)]})


def test_a_composition_needs_a_part() -> None:
    with pytest.raises(ValidationError):
        FiberComposition.model_validate({"parts": []})
