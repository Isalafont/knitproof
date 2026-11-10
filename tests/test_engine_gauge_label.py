"""Écart entre l’échantillon et l’étiquette, dès 5 % (CLA-66, question 14)."""

from decimal import Decimal

from knitproof.domain.gauge import GaugeRange, LabelGauge
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.engine.gauge import gauge_differs_from_label

BIGGER = "trop de mailles pour 10 cm : aiguilles plus grosses"
FINER = "pas assez de mailles pour 10 cm : aiguilles plus fines"
ROWS_TEXT = "ta jauge en rangs diffère de l’étiquette ; la hauteur est calculée sur ton échantillon"


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def inches(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.IN)


def swatch(stitches: str, width: Length | None = None) -> SwatchMeasurement:
    return SwatchMeasurement(stitches=Decimal(stitches), width=width or cm("10"))


def value_label(stitches: str, width: Length | None = None) -> LabelGauge:
    return LabelGauge(stitches=Decimal(stitches), width=width or cm("10"))


def range_label(low: str, high: str) -> LabelGauge:
    return LabelGauge(stitches=GaugeRange(low=Decimal(low), high=Decimal(high)), width=cm("10"))


def rows_swatch(rows: str) -> SwatchMeasurement:
    return SwatchMeasurement(
        stitches=Decimal(20), width=cm("10"), rows=Decimal(rows), height=cm("10")
    )


def rows_label(rows: str | tuple[str, str]) -> LabelGauge:
    value = (
        Decimal(rows)
        if isinstance(rows, str)
        else GaugeRange(low=Decimal(rows[0]), high=Decimal(rows[1]))
    )
    return LabelGauge(stitches=Decimal(20), width=cm("10"), rows=value, height=cm("10"))


def only(notices: tuple[Notice, ...]) -> Notice:
    (notice,) = notices
    assert notice.code is NoticeCode.GAUGE_DIFFERS_FROM_LABEL
    assert notice.status is NoticeStatus.WARNING
    return notice


def test_a_gap_below_five_percent_gives_nothing() -> None:
    # 20 contre 21 : 1/21, soit 4,76 %.
    assert gauge_differs_from_label(swatch("20"), value_label("21")) == ()


def test_a_gap_of_exactly_five_percent_warns() -> None:
    # 21 contre 20 : 1/20, exactement 5 %.
    assert BIGGER in only(gauge_differs_from_label(swatch("21"), value_label("20"))).text


def test_too_few_stitches_say_finer_needles() -> None:
    assert FINER in only(gauge_differs_from_label(swatch("18"), value_label("20"))).text


def test_a_swatch_above_the_range_is_measured_at_the_nearest_bound() -> None:
    # 23 contre 18 à 21 : écart à 21, soit 9,5 %.
    notice = only(gauge_differs_from_label(swatch("23"), range_label("18", "21")))
    assert BIGGER in notice.text


def test_a_swatch_below_the_range_says_finer_needles() -> None:
    assert FINER in only(gauge_differs_from_label(swatch("17"), range_label("18", "21"))).text


def test_a_swatch_inside_the_range_gives_nothing() -> None:
    assert gauge_differs_from_label(swatch("19"), range_label("18", "21")) == ()


def test_a_swatch_just_below_five_percent_of_the_bound_gives_nothing() -> None:
    # 22 contre 18 à 21 : 1/21, soit 4,76 %.
    assert gauge_differs_from_label(swatch("22"), range_label("18", "21")) == ()


def test_widths_in_inches_and_in_cm_are_compared_exactly() -> None:
    # 4 po = 10,16 cm ; 8,4 m sur 10,16 cm contre 8 m sur 4 po : exactement 5 %.
    label = value_label("8", inches("4"))
    assert BIGGER in only(gauge_differs_from_label(swatch("8.4", cm("10.16")), label)).text
    assert gauge_differs_from_label(swatch("8", cm("10.16")), label) == ()


def test_rows_gap_of_five_percent_warns_without_needle_advice() -> None:
    notice = only(gauge_differs_from_label(rows_swatch("21"), rows_label("20")))
    assert notice.text == ROWS_TEXT
    assert "aiguilles" not in notice.text


def test_rows_gap_below_five_percent_gives_nothing() -> None:
    assert gauge_differs_from_label(rows_swatch("20"), rows_label("21")) == ()


def test_rows_inside_the_range_give_nothing() -> None:
    assert gauge_differs_from_label(rows_swatch("29"), rows_label(("28", "30"))) == ()


def test_rows_outside_the_range_warn() -> None:
    assert only(gauge_differs_from_label(rows_swatch("34"), rows_label(("28", "30")))).text == (
        ROWS_TEXT
    )


def test_a_label_without_rows_is_not_compared_on_rows() -> None:
    assert gauge_differs_from_label(rows_swatch("40"), value_label("20")) == ()


def test_a_swatch_without_rows_is_not_compared_on_rows() -> None:
    assert gauge_differs_from_label(swatch("20"), rows_label("20")) == ()


def test_stitches_and_rows_in_gap_give_one_notice_each() -> None:
    swatch_both = SwatchMeasurement(
        stitches=Decimal(24), width=cm("10"), rows=Decimal(40), height=cm("10")
    )
    label_both = LabelGauge(stitches=Decimal(20), width=cm("10"), rows=Decimal(30), height=cm("10"))
    notices = gauge_differs_from_label(swatch_both, label_both)
    assert [notice.text.count("aiguilles") > 0 for notice in notices] == [True, False]
