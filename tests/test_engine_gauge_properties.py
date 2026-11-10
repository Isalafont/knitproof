"""Propriétés de la résolution de la jauge (CLA-66)."""

import re
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from knitproof.domain.gauge import GaugeRange, GaugeSource, LabelGauge
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.engine.gauge import gauge_differs_from_label, resolve_gauge

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


RANGES = st.tuples(STITCHES, STITCHES).filter(lambda pair: pair[0] < pair[1])


@given(swatch_stitches=STITCHES, bounds=RANGES)
def test_no_notice_inside_the_range_and_never_a_needle_size(
    swatch_stitches: Decimal, bounds: tuple[Decimal, Decimal]
) -> None:
    width = Length(value=Decimal(10), unit=LengthUnit.CM)
    label = LabelGauge(stitches=GaugeRange(low=bounds[0], high=bounds[1]), width=width)
    notices = gauge_differs_from_label(
        SwatchMeasurement(stitches=swatch_stitches, width=width), label
    )
    if bounds[0] <= swatch_stitches <= bounds[1]:
        assert notices == ()
    for notice in notices:
        assert not re.search(r"\d\s*mm|\bUS\b|\bUK\b", notice.text)


@given(swatch_stitches=STITCHES, label_stitches=STITCHES)
def test_the_direction_follows_the_sign_of_the_gap(
    swatch_stitches: Decimal, label_stitches: Decimal
) -> None:
    width = Length(value=Decimal(10), unit=LengthUnit.CM)
    notices = gauge_differs_from_label(
        SwatchMeasurement(stitches=swatch_stitches, width=width),
        LabelGauge(stitches=label_stitches, width=width),
    )
    for notice in notices:
        if "aiguilles plus grosses" in notice.text:
            assert swatch_stitches > label_stitches
        else:
            assert "aiguilles plus fines" in notice.text
            assert swatch_stitches < label_stitches
