"""Propriétés de la résolution de la jauge (CLA-66)."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.gauge import GaugeSource, LabelGauge
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.engine.gauge import resolve_gauge

STITCHES = st.integers(min_value=1, max_value=60).map(Decimal)
SWATCHES = st.builds(
    SwatchMeasurement,
    stitches=STITCHES,
    width=st.just(Length(value=Decimal(10), unit=LengthUnit.CM)),
)
LABELS = st.builds(
    LabelGauge,
    stitches=STITCHES,
    width=st.just(Length(value=Decimal(10), unit=LengthUnit.CM)),
)


@given(
    blocked=st.none() | SWATCHES,
    unblocked=st.none() | SWATCHES,
    unknown=st.none() | SWATCHES,
    label=st.none() | LABELS,
)
def test_a_swatch_of_the_person_always_beats_the_label(
    blocked: SwatchMeasurement | None,
    unblocked: SwatchMeasurement | None,
    unknown: SwatchMeasurement | None,
    label: LabelGauge | None,
) -> None:
    resolved = resolve_gauge(blocked=blocked, unblocked=unblocked, unknown=unknown, label=label)
    if blocked is not None or unblocked is not None or unknown is not None:
        assert resolved.source is not GaugeSource.LABEL
    if blocked is not None:
        assert resolved.gauge == blocked
