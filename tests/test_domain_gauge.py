"""Jauge d’étiquette et jauge résolue (CLA-66)."""

from decimal import Decimal

import pytest
import yaml
from pydantic import ValidationError

from knitproof.domain.gauge import GaugeRange, GaugeSource, LabelGauge, ResolvedGauge
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.question import PendingQuestion


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


@pytest.mark.parametrize(("low", "high"), [("22", "20"), ("20", "20")])
def test_a_range_refuses_low_not_below_high(low: str, high: str) -> None:
    with pytest.raises(ValidationError):
        GaugeRange.model_validate({"low": low, "high": high})


def test_a_range_refuses_floats() -> None:
    with pytest.raises(ValidationError, match="float refusé"):
        GaugeRange.model_validate({"low": 20.5, "high": "22"})


def test_a_range_is_frozen_and_forbids_extra_keys() -> None:
    gauge_range = GaugeRange(low=Decimal(20), high=Decimal(22))
    with pytest.raises(ValidationError):
        gauge_range.low = Decimal(19)  # type: ignore[misc]
    with pytest.raises(ValidationError):
        GaugeRange.model_validate({"low": "20", "high": "22", "mid": "21"})


def test_label_stitches_read_from_yaml_as_a_value() -> None:
    data = yaml.safe_load('{stitches: "20", width: {value: "10", unit: cm}}')
    label = LabelGauge.model_validate(data)
    assert label.stitches == Decimal(20)
    assert not isinstance(label.stitches, GaugeRange)


def test_label_stitches_read_from_yaml_as_a_range() -> None:
    # Fixe l’union `left_to_right` : une fourchette ne devient jamais un `Decimal`.
    data = yaml.safe_load('{stitches: {low: "20", high: "22"}, width: {value: "10", unit: cm}}')
    label = LabelGauge.model_validate(data)
    assert label.stitches == GaugeRange(low=Decimal(20), high=Decimal(22))


def test_label_rows_read_as_a_value_or_a_range() -> None:
    value = LabelGauge.model_validate(
        {"stitches": "20", "width": {"value": "10", "unit": "cm"}, "rows": "28"}
        | {"height": {"value": "10", "unit": "cm"}}
    )
    ranged = LabelGauge.model_validate(
        {"stitches": "20", "width": {"value": "10", "unit": "cm"}}
        | {"rows": {"low": "28", "high": "30"}, "height": {"value": "10", "unit": "cm"}}
    )
    assert value.rows == Decimal(28)
    assert ranged.rows == GaugeRange(low=Decimal(28), high=Decimal(30))


@pytest.mark.parametrize("extra", [{"rows": "28"}, {"height": {"value": "10", "unit": "cm"}}])
def test_label_rows_and_height_go_together(extra: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="vont ensemble"):
        LabelGauge.model_validate(
            {"stitches": "20", "width": {"value": "10", "unit": "cm"}} | extra
        )


def test_label_gauge_refuses_floats_and_extra_keys() -> None:
    base = {"stitches": "20", "width": {"value": "10", "unit": "cm"}}
    with pytest.raises(ValidationError):
        LabelGauge.model_validate({**base, "stitches": 20.5})
    with pytest.raises(ValidationError):
        LabelGauge.model_validate({**base, "brand": "x"})


def test_label_gauge_is_frozen() -> None:
    label = LabelGauge(stitches=Decimal(20), width=cm("10"))
    with pytest.raises(ValidationError):
        label.stitches = Decimal(21)  # type: ignore[misc]


def test_a_resolved_gauge_carries_a_measurement_and_its_source() -> None:
    measurement = SwatchMeasurement(stitches=Decimal(20), width=cm("10"))
    resolved = ResolvedGauge(gauge=measurement, source=GaugeSource.BLOCKED)
    assert resolved.gauge == measurement
    assert resolved.notices == ()
    assert resolved.questions == ()


def test_a_resolved_gauge_without_measurement_has_no_source() -> None:
    question = PendingQuestion(code="gauge_missing", text="Quelle jauge ?", options=())
    resolved = ResolvedGauge(gauge=None, source=None, questions=(question,))
    assert resolved.gauge is None
    with pytest.raises(ValidationError, match="source"):
        ResolvedGauge(gauge=None, source=GaugeSource.LABEL)


def test_a_resolved_gauge_with_a_measurement_needs_a_source() -> None:
    measurement = SwatchMeasurement(stitches=Decimal(20), width=cm("10"))
    with pytest.raises(ValidationError, match="source"):
        ResolvedGauge(gauge=measurement, source=None)
