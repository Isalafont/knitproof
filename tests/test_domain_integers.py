"""Entiers du domaine : un `bool` n’est jamais un nombre."""

import importlib
import inspect
import pkgutil
from decimal import Decimal
from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

import knitproof.domain
from knitproof.domain.cast_on import CastOnCheck, CastOnResult, RoundingRule, StitchMultiple
from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.location import SourceLocation
from knitproof.domain.measure import Length, LengthUnit
from knitproof.domain.pattern import Pattern, RepeatBlock, Round, Work
from knitproof.domain.simulation import RoundCount

VALID: dict[type[BaseModel], dict[str, object]] = {
    Work: {"work": 10},
    RepeatBlock: {"body": ("k2tog",), "times": 2},
    Round: {"start": 1, "end": 2, "ops": ({"work": 10},), "stated_count": 10},
    Pattern: {"cast_on": 10, "rounds": ({"start": 1, "ops": ({"work": 10},)},)},
    StitchMultiple: {"repeat_multiple": 4, "repeat_offset": 0},
    CastOnResult: {
        "target": Length(value=Decimal(43), unit=LengthUnit.CM),
        "raw_stitches": Decimal(86),
        "stitches": 84,
        "rounding_rule": RoundingRule.NEAREST_TIE_DOWN,
        "finished_cm": Decimal(42),
    },
    CastOnCheck: {
        "proposed": 88,
        "expected": 88,
        "reasons": (),
        "proposed_finished_cm": Decimal(44),
    },
    Finding: {
        "status": FindingStatus.ERROR,
        "code": FindingCode.COUNT_MISMATCH,
        "round": 1,
        "expected": 10,
        "actual": 9,
    },
    SourceLocation: {"page": 1, "line": 3},
    RoundCount: {"round": 1, "stitches": 10},
}


def _is_int(annotation: object) -> bool:
    """`int`, éventuellement dans un `Annotated` ou une union avec `None`."""
    return annotation is int or any(_is_int(arg) for arg in get_args(annotation))


def _int_fields(model: type[BaseModel]) -> list[str]:
    return [name for name, field in model.model_fields.items() if _is_int(field.annotation)]


def _domain_models() -> set[type[BaseModel]]:
    models: set[type[BaseModel]] = set()
    for info in pkgutil.iter_modules(knitproof.domain.__path__):
        module = importlib.import_module(f"knitproof.domain.{info.name}")
        for _, value in inspect.getmembers(module, inspect.isclass):
            if issubclass(value, BaseModel) and value.__module__ == module.__name__:
                models.add(value)
    return models


def test_every_domain_model_with_an_integer_is_listed() -> None:
    assert {m for m in _domain_models() if _int_fields(m)} == set(VALID)


CASES = [(model, name) for model in VALID for name in _int_fields(model)]


@pytest.mark.parametrize(("model", "name"), CASES, ids=[f"{m.__name__}.{n}" for m, n in CASES])
def test_a_bool_is_refused_where_an_integer_is_expected(model: type[BaseModel], name: str) -> None:
    model.model_validate(VALID[model])
    with pytest.raises(ValidationError) as error:
        model.model_validate({**VALID[model], name: True})

    assert [e["loc"] for e in error.value.errors()] == [(name,)]
