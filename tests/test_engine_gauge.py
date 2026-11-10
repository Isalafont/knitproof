"""Résolution de la jauge selon l’ordre de confiance (CLA-66, ADR 0008)."""

from decimal import Decimal

from knitproof.domain.gauge import GaugeRange, GaugeSource, LabelGauge
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.notice import NoticeCode, NoticeStatus
from knitproof.engine.gauge import resolve_gauge


def cm(value: str) -> Length:
    return Length(value=Decimal(value), unit=LengthUnit.CM)


def swatch(stitches: str) -> SwatchMeasurement:
    return SwatchMeasurement(stitches=Decimal(stitches), width=cm("10"))


def label(stitches: Decimal | GaugeRange) -> LabelGauge:
    return LabelGauge(stitches=stitches, width=cm("10"))


def test_a_blocked_swatch_is_followed_without_notice() -> None:
    resolved = resolve_gauge(blocked=swatch("20"), unblocked=swatch("22"))
    assert resolved.gauge == swatch("20")
    assert resolved.source is GaugeSource.BLOCKED
    assert resolved.notices == ()
    assert resolved.questions == ()


def test_an_unblocked_swatch_alone_is_followed_with_advice_to_block_it() -> None:
    resolved = resolve_gauge(unblocked=swatch("22"))
    assert resolved.gauge == swatch("22")
    assert resolved.source is GaugeSource.UNBLOCKED
    (notice,) = resolved.notices
    assert notice.code is NoticeCode.GAUGE_UNBLOCKED
    assert notice.status is NoticeStatus.WARNING
    assert notice.text.startswith("À VÉRIFIER")
    assert "bloquer (laver puis sécher)" in notice.text
    assert resolved.questions == ()


def test_an_unknown_blocking_state_asks_and_gives_no_gauge() -> None:
    resolved = resolve_gauge(unknown=swatch("21"))
    assert resolved.gauge is None
    assert resolved.source is None
    (question,) = resolved.questions
    assert question.code == NoticeCode.GAUGE_BLOCKING_UNKNOWN
    assert "L’as-tu bloqué (lavé puis séché) ?" in question.text
    assert question.options == ("oui", "non")
    assert "unknown_blocking" in question.text
    assert "after_blocking" in question.text
    assert "before_blocking" in question.text


def test_an_unknown_blocking_state_is_not_replaced_by_the_label() -> None:
    resolved = resolve_gauge(unknown=swatch("21"), label=label(Decimal(20)))
    assert resolved.gauge is None
    assert [question.code for question in resolved.questions] == ["gauge_blocking_unknown"]


def test_a_label_value_alone_is_followed_with_a_review_notice_and_advice() -> None:
    resolved = resolve_gauge(label=label(Decimal(20)))
    assert resolved.gauge == swatch("20")
    assert resolved.source is GaugeSource.LABEL
    (notice,) = resolved.notices
    assert notice.code is NoticeCode.GAUGE_FROM_LABEL
    assert notice.text.startswith("À VÉRIFIER : jauge du fabricant, état de blocage inconnu")
    assert "échantillon" in notice.text
    assert resolved.questions == ()


def test_a_label_with_rows_gives_them_to_the_gauge() -> None:
    resolved = resolve_gauge(
        label=LabelGauge(stitches=Decimal(20), width=cm("10"), rows=Decimal(28), height=cm("10"))
    )
    assert resolved.gauge is not None
    assert resolved.gauge.rows_per_10_cm == Decimal(28)


def test_a_label_range_alone_asks_which_value_to_keep() -> None:
    resolved = resolve_gauge(label=label(GaugeRange(low=Decimal(20), high=Decimal(22))))
    assert resolved.gauge is None
    assert resolved.notices == ()
    (question,) = resolved.questions
    assert question.code == NoticeCode.LABEL_GAUGE_RANGE
    assert "quelle valeur de la fourchette retenir ?" in question.text


def test_a_label_row_range_asks_which_value_to_keep_and_gives_no_gauge() -> None:
    resolved = resolve_gauge(
        label=LabelGauge(
            stitches=Decimal(20),
            width=cm("10"),
            rows=GaugeRange(low=Decimal(28), high=Decimal(32)),
            height=cm("10"),
        )
    )
    assert resolved.gauge is None
    assert resolved.notices == ()
    (question,) = resolved.questions
    assert question.code == NoticeCode.LABEL_GAUGE_RANGE
    assert "rangs" in question.text
    assert "quelle valeur de la fourchette retenir ?" in question.text


def test_the_label_advice_tells_to_block_the_swatch_then_measure_it() -> None:
    (notice,) = resolve_gauge(label=label(Decimal(20))).notices

    assert "Fais un échantillon, bloque-le (lave-le puis sèche-le), puis mesure-le" in notice.text
    assert notice.text.endswith("pour remplacer la jauge de l’étiquette.")


def test_nothing_asks_for_a_gauge_and_invents_none() -> None:
    resolved = resolve_gauge()
    assert resolved.gauge is None
    assert resolved.source is None
    (question,) = resolved.questions
    assert question.code == NoticeCode.GAUGE_MISSING
