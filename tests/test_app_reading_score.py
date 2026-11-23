"""La lecture juste, champ par champ, sans tolérance (CLA-200)."""

from decimal import Decimal

from knitproof.app.beanie_reading import BeanieReading, ReadEdge, ReadGauge, ReadLength
from knitproof.app.reading_score import FieldOutcome, FieldScore, score_reading
from knitproof.domain.measure import LengthUnit
from knitproof.domain.needle import KnittingMethod


def _cm(value: str) -> ReadLength:
    return ReadLength(value=Decimal(value), unit=LengthUnit.CM)


def _expected() -> BeanieReading:
    return BeanieReading(
        head_circumference=_cm("48"),
        smaller_than_head=_cm("5"),
        gauge_after_blocking=ReadGauge(stitches=Decimal(20), width=_cm("10")),
        needle_mm=(Decimal("3.5"),),
        edge=ReadEdge.RIB_2X2,
    )


def _outcomes(expected: BeanieReading, read: BeanieReading | None) -> dict[str, FieldOutcome]:
    return {line.field: line.outcome for line in score_reading(expected, read)}


def test_a_perfect_reading_is_exact_where_something_is_expected() -> None:
    outcomes = _outcomes(_expected(), _expected())

    assert outcomes["head_circumference.value"] is FieldOutcome.EXACT
    assert outcomes["head_circumference.unit"] is FieldOutcome.EXACT
    assert outcomes["gauge_after_blocking.stitches"] is FieldOutcome.EXACT
    assert outcomes["gauge_after_blocking.width.unit"] is FieldOutcome.EXACT
    assert outcomes["needle_mm"] is FieldOutcome.EXACT
    assert outcomes["edge"] is FieldOutcome.EXACT


def test_what_nobody_expects_nor_reads_is_a_correct_abstention() -> None:
    outcomes = _outcomes(_expected(), _expected())

    assert outcomes["finished_circumference.value"] is FieldOutcome.CORRECT_ABSTENTION
    assert outcomes["label_gauge.stitches"] is FieldOutcome.CORRECT_ABSTENTION
    assert outcomes["worked"] is FieldOutcome.CORRECT_ABSTENTION


def test_a_different_value_is_wrong_without_tolerance() -> None:
    read = _expected().model_copy(update={"head_circumference": _cm("48.1")})

    outcomes = _outcomes(_expected(), read)

    assert outcomes["head_circumference.value"] is FieldOutcome.WRONG
    assert outcomes["head_circumference.unit"] is FieldOutcome.EXACT


def test_a_value_read_where_none_is_expected_is_invented() -> None:
    read = _expected().model_copy(update={"worked": KnittingMethod.ROUND})

    assert _outcomes(_expected(), read)["worked"] is FieldOutcome.INVENTED


def test_nothing_read_where_something_is_expected_is_missed() -> None:
    read = _expected().model_copy(update={"edge": None, "needle_mm": ()})

    outcomes = _outcomes(_expected(), read)

    assert outcomes["edge"] is FieldOutcome.MISSED
    assert outcomes["needle_mm"] is FieldOutcome.MISSED


def test_needles_are_compared_as_a_whole() -> None:
    read = _expected().model_copy(update={"needle_mm": (Decimal("3.5"), Decimal(4))})

    assert _outcomes(_expected(), read)["needle_mm"] is FieldOutcome.WRONG


def test_ten_equals_ten_point_zero_as_a_value() -> None:
    read = _expected().model_copy(
        update={"gauge_after_blocking": ReadGauge(stitches=Decimal("20.0"), width=_cm("10.00"))}
    )

    assert _outcomes(_expected(), read)["gauge_after_blocking.width.value"] is FieldOutcome.EXACT


def test_a_refusal_misses_every_expected_field_and_invents_nothing() -> None:
    outcomes = _outcomes(_expected(), None)

    assert outcomes["head_circumference.value"] is FieldOutcome.MISSED
    assert outcomes["edge"] is FieldOutcome.MISSED
    assert outcomes["worked"] is FieldOutcome.CORRECT_ABSTENTION
    assert FieldOutcome.INVENTED not in outcomes.values()


def test_one_line_per_leaf_field() -> None:
    lines = score_reading(_expected(), _expected())

    assert len(lines) == len({line.field for line in lines})
    assert lines[0] == FieldScore(field="head_circumference.value", outcome=FieldOutcome.EXACT)
