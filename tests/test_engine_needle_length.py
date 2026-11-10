"""Aiguille et calotte : passage en magic loop (CLA-68, ADR 0023)."""

import datetime
from decimal import Decimal

from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.crown import Crown
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.needle import Needle, NeedleKind, NeedleSize, NeedleSystem
from knitproof.domain.notice import NoticeCode, NoticeStatus
from knitproof.domain.provenance import SourceKind
from knitproof.engine.crown import crown_plan
from knitproof.engine.needle_length import needle_change

SOURCE = {
    "kind": SourceKind.PERSON_DECISION,
    "reference": "Isabelle, ADR 0019",
    "read_on": datetime.date(2026, 11, 2),
}
RULE = CrownRule.model_validate(
    {
        "id": "calotte",
        "source": SOURCE,
        "decreases_per_round": 8,
        "last_round_below": 24,
        "min_cast_on": 32,
        "every_round_last": 3,
    }
)
ADVICE = MagicLoopAdvice.model_validate(
    {
        "id": "magic-loop-cable",
        "magic_loop_cable": {"value": "80", "unit": "cm"},
        "source": {
            "kind": SourceKind.REFERENCE_MEASUREMENT,
            "reference": "ADR 0023 §6",
            "read_on": datetime.date(2026, 11, 2),
        },
    }
)


def swatch(stitches: str) -> SwatchMeasurement:
    return SwatchMeasurement(
        stitches=Decimal(stitches), width=Length(value=Decimal(10), unit=LengthUnit.CM)
    )


def circular(length: str | None) -> Needle:
    cable = None if length is None else Length(value=Decimal(length), unit=LengthUnit.CM)
    return Needle(
        size=NeedleSize(system=NeedleSystem.US, original="6"),
        kind=NeedleKind.CIRCULAR,
        cable_length=cable,
    )


def crown_of_88() -> Crown:
    return crown_plan(88, RULE)


def test_a_40_cm_needle_on_the_unwashed_gauge_changes_at_round_2() -> None:
    notice = needle_change(crown_of_88(), circular("40"), swatch("20"), swatch("22"), ADVICE)

    assert notice is not None
    assert (notice.status, notice.code, notice.round) == (
        NoticeStatus.WARNING,
        NoticeCode.NEEDLE_CHANGE,
        2,
    )
    assert "À VÉRIFIER" not in notice.text


def test_with_only_the_washed_gauge_the_change_is_at_round_4_and_to_verify() -> None:
    notice = needle_change(crown_of_88(), circular("40"), swatch("20"), None, ADVICE)

    assert notice is not None
    assert (notice.code, notice.round) == (NoticeCode.NEEDLE_CHANGE, 4)
    assert "À VÉRIFIER : jauge après blocage" in notice.text


def test_the_text_proposes_magic_loop_or_double_pointed_needles() -> None:
    notice = needle_change(crown_of_88(), circular("40"), swatch("20"), swatch("22"), ADVICE)

    assert notice is not None
    assert "magic loop" in notice.text
    assert "80 cm" in notice.text
    assert "doubles pointes" in notice.text


def test_a_needle_longer_than_the_body_warns_without_a_change() -> None:
    notice = needle_change(crown_of_88(), circular("60"), swatch("20"), swatch("22"), ADVICE)

    assert notice is not None
    assert (notice.status, notice.code, notice.round) == (
        NoticeStatus.WARNING,
        NoticeCode.NEEDLE_TOO_LONG,
        None,
    )


def test_double_pointed_needles_give_nothing() -> None:
    needle = Needle(
        size=NeedleSize(system=NeedleSystem.US, original="6"), kind=NeedleKind.DOUBLE_POINTED
    )

    assert needle_change(crown_of_88(), needle, swatch("20"), swatch("22"), ADVICE) is None


def test_a_circular_without_a_length_is_advised_at_the_start_of_the_crown() -> None:
    notice = needle_change(crown_of_88(), circular(None), swatch("20"), swatch("22"), ADVICE)

    assert notice is not None
    assert (notice.code, notice.round) == (NoticeCode.NEEDLE_CHANGE, 1)
    assert "quand le tricot se tend sur l’aiguille" in notice.text


def test_a_length_equal_to_the_circumference_is_accepted() -> None:
    # 88 m à 22 m/10 cm : 40 cm exactement.
    notice = needle_change(crown_of_88(), circular("40"), swatch("22"), swatch("22"), ADVICE)

    assert notice is not None
    assert notice.code is NoticeCode.NEEDLE_CHANGE
