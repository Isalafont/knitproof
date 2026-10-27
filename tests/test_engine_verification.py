"""`verify` : constats sur les comptes annoncés et les répétitions (CLA-64)."""

from pathlib import Path

import yaml

from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.location import SourceLocation
from knitproof.domain.pattern import Pattern, Round, Work
from knitproof.engine.verification import simulate, verify

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _load(name: str) -> Pattern:
    text = (EXAMPLES / name).read_text(encoding="utf-8")
    return Pattern.model_validate(yaml.safe_load(text))


def test_stated_count_differing_from_the_simulated_one_is_reported() -> None:
    findings = verify(_load("bonnet-erreur-rang-33.yaml"))

    assert findings == [
        Finding(
            status=FindingStatus.ERROR,
            code=FindingCode.COUNT_MISMATCH,
            round=33,
            expected=90,
            actual=89,
            location=SourceLocation(page=2, line=14),
        )
    ]


def test_range_stated_count_is_compared_at_its_last_round() -> None:
    pattern = Pattern(
        cast_on=10,
        rounds=(Round(start=1, end=3, ops=(Work(work=10),), stated_count=9),),
    )

    findings = verify(pattern)

    assert [(f.code, f.round, f.expected, f.actual) for f in findings] == [
        (FindingCode.COUNT_MISMATCH, 3, 10, 9)
    ]


def test_mismatch_then_repeat_not_fitting_are_both_reported_in_round_order() -> None:
    pattern = Pattern(
        cast_on=10,
        rounds=(
            Round(start=1, ops=(Work(work=10),), stated_count=9),
            Round(start=2, ops=(Work(work=12),)),
        ),
    )

    findings = verify(pattern)

    assert [(f.code, f.round) for f in findings] == [
        (FindingCode.COUNT_MISMATCH, 1),
        (FindingCode.REPEAT_NOT_FITTING, 2),
    ]


def test_stated_count_after_the_halt_is_not_compared() -> None:
    pattern = Pattern(
        cast_on=10,
        rounds=(
            Round(start=1, ops=(Work(work=12),)),
            Round(start=2, ops=(Work(work=12),), stated_count=5),
        ),
    )

    findings = verify(pattern)

    assert [f.code for f in findings] == [FindingCode.REPEAT_NOT_FITTING]


def test_right_synthetic_beanie_has_no_finding() -> None:
    assert verify(_load("bonnet-synthetique.yaml")) == []


def test_right_synthetic_beanie_ends_on_eight_stitches() -> None:
    simulation = simulate(_load("bonnet-synthetique.yaml"))

    assert len(simulation.counts) == 56
    assert simulation.counts[-1].stitches == 8
