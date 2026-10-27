"""Opérations, tours et patron : invariants structurels (CLA-64)."""

import pytest
from pydantic import TypeAdapter, ValidationError

from knitproof.domain.pattern import Op, Repeat, RepeatBlock, Stitch, Work

OP_ADAPTER: TypeAdapter[Op] = TypeAdapter(Op)


def test_work_consumes_and_produces_its_stitches() -> None:
    work = Work(work=10)

    assert (work.consumes, work.produces) == (10, 10)


def test_work_of_zero_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Work(work=0)


def test_k2tog_consumes_two_and_produces_one() -> None:
    assert (Stitch.K2TOG.consumes, Stitch.K2TOG.produces) == (2, 1)


def test_m1_consumes_none_and_produces_one() -> None:
    assert (Stitch.M1.consumes, Stitch.M1.produces) == (0, 1)


def test_repeat_sums_its_body_times() -> None:
    repeat = Repeat(repeat=RepeatBlock(body=(Work(work=9), Stitch.K2TOG), times=9))

    assert (repeat.consumes, repeat.produces) == (99, 90)


def test_nested_repeat_is_computed() -> None:
    inner = Repeat(repeat=RepeatBlock(body=(Work(work=1), Stitch.K2TOG), times=2))
    outer = Repeat(repeat=RepeatBlock(body=(inner, Stitch.M1), times=3))

    assert (outer.consumes, outer.produces) == (18, 15)


def test_repeat_with_empty_body_is_rejected() -> None:
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python({"repeat": {"body": [], "times": 2}})


def test_repeat_with_zero_times_is_rejected() -> None:
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python({"repeat": {"body": ["k2tog"], "times": 0}})


def test_yaml_shapes_are_parsed() -> None:
    op = OP_ADAPTER.validate_python({"repeat": {"body": [{"work": 9}, "k2tog"], "times": 9}})

    assert isinstance(op, Repeat)
    assert (op.consumes, op.produces) == (99, 90)


@pytest.mark.parametrize(
    "raw",
    ["ssk", {"work": 3, "extra": 1}, {"foo": 1}, 3],
)
def test_unknown_operation_is_rejected(raw: object) -> None:
    with pytest.raises(ValidationError):
        OP_ADAPTER.validate_python(raw)


@pytest.mark.parametrize("raw", [{"foo": 1}, 3])
def test_unrecognised_shape_has_no_tag(raw: object) -> None:
    with pytest.raises(ValidationError) as error:
        OP_ADAPTER.validate_python(raw)

    assert error.value.errors()[0]["type"] == "union_tag_not_found"
