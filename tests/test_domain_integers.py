"""Entiers du domaine : un `bool` n’est jamais un nombre."""

import datetime
import importlib
import inspect
import pkgutil
from decimal import Decimal
from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

import knitproof.domain
from knitproof.domain.age import Age
from knitproof.domain.beanie import BeaniePlan, RowCount, RowRounding
from knitproof.domain.cast_on import (
    CastOnCheck,
    CastOnResult,
    FlatCastOn,
    RoundingRule,
    StitchMultiple,
)
from knitproof.domain.construction import CrownRule
from knitproof.domain.crown import Crown
from knitproof.domain.ease import EaseSize
from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.location import SourceLocation
from knitproof.domain.measure import Length, LengthUnit
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.pattern import Pattern, RepeatBlock, Round, Work
from knitproof.domain.reference import AgeBounds
from knitproof.domain.report import DecidedBy, ReportEntry, ReportStatus
from knitproof.domain.simulation import RoundCount
from knitproof.domain.transition import Transition, TransitionRefusal, TransitionRejection

VALID: dict[type[BaseModel], dict[str, object]] = {
    Age: {"value": 3, "unit": "years"},
    AgeBounds: {"min_months": 3, "max_months": 6},
    CrownRule: {
        "id": "calotte",
        "source": {
            "kind": "person_decision",
            "reference": "Isabelle, ADR 0019",
            "read_on": datetime.date(2026, 11, 2),
        },
        "decreases_per_round": 8,
        "last_round_below": 24,
        "min_cast_on": 32,
        "every_round_last": 3,
    },
    Crown: {
        "stitches": 10,
        "rounds": ({"start": 1, "ops": ({"work": 10},)},),
        "decrease_rounds": 1,
        "remaining": 10,
    },
    EaseSize: {"head": {"low": "47", "high": "48", "unit": "cm"}, "cast_on": 92},
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
    FlatCastOn: {
        "body": {
            "target": Length(value=Decimal(43), unit=LengthUnit.CM),
            "raw_stitches": Decimal(86),
            "stitches": 84,
            "rounding_rule": RoundingRule.NEAREST_TIE_DOWN,
            "finished_cm": Decimal(42),
        },
        "selvedges": 2,
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
    BeaniePlan: {
        "worked": "round",
        "cast_on": 10,
        "rows": {
            "total": {"raw": Decimal(3), "rows": 3, "rule": RowRounding.NEAREST_TIE_DOWN},
            "brim": {"raw": Decimal(1), "rows": 1, "rule": RowRounding.NEAREST_TIE_DOWN},
        },
        "body": {"raw": Decimal(1), "rows": 1, "rule": RowRounding.DIFFERENCE},
        "crown": {
            "stitches": 10,
            "rounds": ({"start": 1, "ops": ({"work": 10},)},),
            "decrease_rounds": 1,
            "remaining": 10,
        },
        "depth_cm": Decimal(1),
        "finished_height": Length(value=Decimal(20), unit=LengthUnit.CM),
        "pattern": {"cast_on": 10, "rounds": ({"start": 1, "ops": ({"work": 10},)},)},
    },
    RowCount: {"raw": Decimal(75), "rows": 75, "rule": RowRounding.NEAREST_TIE_DOWN},
    Notice: {
        "status": NoticeStatus.WARNING,
        "code": NoticeCode.NEEDLE_CHANGE,
        "text": "t",
        "round": 2,
    },
    ReportEntry: {
        "status": ReportStatus.ERROR,
        "code": "count_mismatch",
        "round": 1,
        "lines": ("t",),
        "decided_by": DecidedBy.ENGINE,
    },
    SourceLocation: {"page": 1, "line": 3},
    RoundCount: {"round": 1, "stitches": 10},
    Transition: {
        "edge_stitches": 4,
        "body_stitches": 3,
        "adjustment_round": {"start": 1, "ops": ({"work": 2}, "k2tog"), "stated_count": 3},
    },
    TransitionRefusal: {
        "edge_stitches": 88,
        "body_stitches": 43,
        "reason": TransitionRejection.TOO_MANY_DECREASES,
        "limit": 44,
    },
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
