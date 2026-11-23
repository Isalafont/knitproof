"""La lecture d’une demande de bonnet et sa conversion en entrées du moteur (CLA-200)."""

import datetime
from decimal import Decimal
from importlib.resources import files

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from knitproof.app.beanie_reading import (
    EDGE_MULTIPLES,
    BeanieReading,
    ReadEdge,
    ReadGauge,
    ReadingIncomplete,
    ReadingInputs,
    ReadingRecord,
    ReadLength,
    reading_inputs,
)
from knitproof.app.beanie_request import BeanieRequest
from knitproof.domain.measure import LengthUnit
from knitproof.domain.provenance import Provenance, SourceKind
from knitproof.domain.reading import ModelReading

_EXAMPLE = files("knitproof") / "evals" / "data" / "dev" / "exemple-bonnet-3-ans.yaml"


def _cm(value: str) -> ReadLength:
    return ReadLength(value=Decimal(value), unit=LengthUnit.CM)


def _inputs(reading: BeanieReading) -> ReadingInputs:
    inputs = reading_inputs(reading)
    assert isinstance(inputs, ReadingInputs), inputs
    return inputs


def _incomplete(reading: BeanieReading) -> ReadingIncomplete:
    result = reading_inputs(reading)
    assert isinstance(result, ReadingIncomplete), result
    return result


def _reading(**changes: object) -> BeanieReading:
    base: dict[str, object] = {
        "head_circumference": _cm("48"),
        "smaller_than_head": _cm("5"),
        "gauge_after_blocking": ReadGauge(stitches=Decimal(20), width=_cm("10")),
        "edge": ReadEdge.RIB_2X2,
    }
    return BeanieReading.model_validate({**base, **changes})


def test_a_reading_is_empty_by_default() -> None:
    reading = BeanieReading()

    assert reading.head_circumference is None
    assert reading.needle_mm == ()
    assert reading.edge is None
    assert reading.worked is None


def test_the_example_reads_as_the_request_of_the_example() -> None:
    request = BeanieRequest.model_validate(yaml.safe_load(_EXAMPLE.read_text("utf-8"))["request"])

    inputs = _inputs(_reading())

    assert inputs.target == request.circumference
    assert inputs.multiple == request.multiple
    assert request.swatch is not None
    assert request.swatch.after_blocking is not None
    assert inputs.blocked is not None
    assert inputs.blocked.stitches == request.swatch.after_blocking.stitches
    assert inputs.blocked.width == request.swatch.after_blocking.width


def test_a_finished_circumference_gives_the_target_without_ease() -> None:
    reading = _reading(
        smaller_than_head=None, finished_circumference=_cm("42"), head_circumference=_cm("46")
    )

    assert _inputs(reading).target.in_cm == Decimal(42)


def test_inches_are_converted_by_the_code() -> None:
    reading = _reading(
        head_circumference=ReadLength(value=Decimal(20), unit=LengthUnit.IN),
        smaller_than_head=_cm("5"),
    )

    assert _inputs(reading).target.in_cm == Decimal("45.80")


def test_a_gauge_over_five_centimetres_is_kept_as_read() -> None:
    reading = _reading(gauge_after_blocking=ReadGauge(stitches=Decimal(9), width=_cm("5")))

    blocked = _inputs(reading).blocked
    assert blocked is not None
    assert blocked.width.in_cm == Decimal(5)
    assert blocked.stitches == Decimal(9)


def test_each_edge_has_its_multiple() -> None:
    assert {edge: EDGE_MULTIPLES[edge] for edge in ReadEdge} == {
        ReadEdge.RIB_1X1: 2,
        ReadEdge.RIB_2X2: 4,
        ReadEdge.ROLLED_STOCKINETTE: 1,
        ReadEdge.GARTER: 1,
    }
    assert _inputs(_reading(edge=ReadEdge.RIB_1X1)).multiple.repeat_multiple == 2


def test_the_other_gauges_are_passed_on() -> None:
    gauge = ReadGauge(stitches=Decimal(22), width=_cm("10"))
    reading = _reading(
        gauge_after_blocking=None,
        gauge_before_blocking=gauge,
        gauge_unknown_blocking=ReadGauge(stitches=Decimal(21), width=_cm("10")),
        label_gauge=ReadGauge(stitches=Decimal(24), width=_cm("10")),
    )

    inputs = _inputs(reading)
    assert inputs.unblocked is not None
    assert inputs.unblocked.stitches == 22
    assert inputs.label is not None
    assert inputs.label.stitches == 24
    assert inputs.unknown is not None
    assert inputs.unknown.stitches == 21
    assert inputs.blocked is None


def test_a_reading_without_gauge_is_still_convertible() -> None:
    inputs = _inputs(_reading(gauge_after_blocking=None))

    assert inputs.blocked is None
    assert inputs.label is None


@pytest.mark.parametrize(
    ("field", "missing"),
    [("head_circumference", "head_circumference"), ("edge", "edge")],
)
def test_a_missing_required_field_names_itself(field: str, missing: str) -> None:
    assert _incomplete(_reading(**{field: None})).field == missing


def test_neither_ease_nor_finished_circumference_is_incomplete() -> None:
    assert _incomplete(_reading(smaller_than_head=None)).field == "smaller_than_head"


def test_both_ease_and_finished_circumference_are_incomplete() -> None:
    assert _incomplete(_reading(finished_circumference=_cm("43"))).field == "finished_circumference"


def test_an_ease_larger_than_the_head_is_incomplete() -> None:
    assert _incomplete(_reading(smaller_than_head=_cm("60"))).field == "smaller_than_head"


def test_a_json_number_is_accepted_for_a_length() -> None:
    reading = BeanieReading.model_validate(
        {"head_circumference": {"value": 45.5, "unit": "cm"}, "needle_mm": [3.5, 4]}
    )

    assert reading.head_circumference == _cm("45.5")
    assert reading.needle_mm == (Decimal("3.5"), Decimal(4))


def test_a_reading_refuses_an_unknown_key_and_a_boolean() -> None:
    with pytest.raises(ValidationError):
        BeanieReading.model_validate({"colour": "rouge"})
    with pytest.raises(ValidationError):
        BeanieReading.model_validate({"head_circumference": {"value": True, "unit": "cm"}})


def test_the_json_schema_announces_a_number() -> None:
    schema = BeanieReading.model_json_schema()

    types = [option["type"] for option in schema["$defs"]["ReadDecimal"]["anyOf"]]
    assert "number" in types


def test_a_record_carries_a_model_inference_provenance() -> None:
    extracted = ModelReading(
        provider="p",
        model="m",
        model_version="v",
        prompt_id="request-reading-v1",
        prompt_sha256="0" * 64,
    )
    provenance = Provenance(
        kind=SourceKind.MODEL_INFERENCE,
        reference="request-reading-v1",
        read_on=datetime.date(2026, 11, 23),
        to_verify=True,
        extracted_by=extracted,
    )

    record = ReadingRecord(reading=_reading(), provenance=provenance)

    assert record.provenance.extracted_by == extracted
    with pytest.raises(ValidationError):
        ReadingRecord(
            reading=_reading(),
            provenance=provenance.model_copy(update={"kind": SourceKind.ENGINE}),
        )


_CM_VALUES = st.decimals(min_value=Decimal(30), max_value=Decimal(70), places=2, allow_nan=False)


@given(head=_CM_VALUES, finished=_CM_VALUES)
def test_a_finished_circumference_read_in_cm_is_the_target(
    head: Decimal, finished: Decimal
) -> None:
    reading = _reading(
        head_circumference=ReadLength(value=head, unit=LengthUnit.CM),
        smaller_than_head=None,
        finished_circumference=ReadLength(value=finished, unit=LengthUnit.CM),
    )

    assert _inputs(reading).target.in_cm == finished
