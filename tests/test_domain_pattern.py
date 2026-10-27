"""Opérations, tours et patron : invariants structurels (CLA-64)."""

from pathlib import Path

import pytest
import yaml
from pydantic import TypeAdapter, ValidationError

from knitproof.domain.location import SourceLocation
from knitproof.domain.pattern import Op, Pattern, Repeat, RepeatBlock, Round, Stitch, Work

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

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


def test_round_ending_before_its_start_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Round(start=5, end=4, ops=(Work(work=10),))


def test_round_last_is_end_or_start() -> None:
    assert Round(start=1, end=30, ops=(Work(work=10),)).last == 30
    assert Round(start=7, ops=(Work(work=10),)).last == 7


def test_round_without_operations_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Round(start=1, ops=())


def test_round_sums_its_operations() -> None:
    round_ = Round(start=1, ops=(Work(work=8), Stitch.K2TOG, Stitch.M1))

    assert (round_.consumes, round_.produces) == (10, 10)


def test_round_count_and_location_are_optional() -> None:
    round_ = Round(start=1, ops=(Work(work=8),))

    assert (round_.stated_count, round_.location) == (None, None)


def test_pattern_must_start_at_round_one() -> None:
    with pytest.raises(ValidationError, match="tour 2"):
        Pattern(cast_on=10, rounds=(Round(start=2, ops=(Work(work=10),)),))


def test_pattern_with_a_gap_is_rejected() -> None:
    with pytest.raises(ValidationError, match="tour 3"):
        Pattern(
            cast_on=10,
            rounds=(
                Round(start=1, ops=(Work(work=10),)),
                Round(start=3, ops=(Work(work=10),)),
            ),
        )


def test_pattern_with_overlapping_rounds_is_rejected() -> None:
    with pytest.raises(ValidationError, match="tour 2"):
        Pattern(
            cast_on=10,
            rounds=(
                Round(start=1, end=3, ops=(Work(work=10),)),
                Round(start=2, ops=(Work(work=10),)),
            ),
        )


def test_pattern_without_rounds_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Pattern(cast_on=10, rounds=())


def test_pattern_with_an_unknown_operation_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Pattern.model_validate({"cast_on": 10, "rounds": [{"start": 1, "ops": ["ssk"]}]})


def test_pattern_with_an_extra_key_in_work_is_rejected() -> None:
    raw = {"cast_on": 10, "rounds": [{"start": 1, "ops": [{"work": 10, "extra": 1}]}]}

    with pytest.raises(ValidationError):
        Pattern.model_validate(raw)


def test_example_with_error_at_round_33_is_a_pattern() -> None:
    text = (EXAMPLES / "bonnet-erreur-rang-33.yaml").read_text(encoding="utf-8")

    pattern = Pattern.model_validate(yaml.safe_load(text))

    assert len(pattern.rounds) == 4
    assert pattern.rounds[-1].start == 33
    assert pattern.rounds[-1].stated_count == 89
    assert pattern.rounds[-1].location == SourceLocation(page=2, line=14)
