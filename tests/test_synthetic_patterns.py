"""Patrons synthétiques justes d’`examples/synthetiques/` : aucun constat (CLA-75)."""

from pathlib import Path

import pytest
import yaml

from knitproof.domain.finding import Finding, FindingCode, FindingStatus
from knitproof.domain.pattern import Pattern
from knitproof.engine.verification import verify

SYNTHETIC = Path(__file__).resolve().parents[1] / "examples" / "synthetiques"
FILES = sorted(SYNTHETIC.glob("**/*.yaml"))
MIN_SIZES_PER_FAMILY = 3


def _load(path: Path) -> Pattern:
    return Pattern.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _id(path: Path) -> str:
    return path.relative_to(SYNTHETIC).as_posix()


@pytest.mark.parametrize("family", ["bonnet-secteurs-"])
def test_each_family_has_at_least_three_sizes(family: str) -> None:
    sizes = [path for path in FILES if path.name.startswith(family)]

    assert len(sizes) >= MIN_SIZES_PER_FAMILY


@pytest.mark.parametrize("path", FILES, ids=_id)
def test_synthetic_pattern_has_no_finding(path: Path) -> None:
    assert verify(_load(path)) == []


@pytest.mark.parametrize("path", FILES, ids=_id)
def test_shifted_stated_count_is_reported_as_a_mismatch(path: Path) -> None:
    pattern = _load(path)
    index, stated = next(
        (i, r.stated_count) for i, r in enumerate(pattern.rounds) if r.stated_count is not None
    )
    shifted = pattern.rounds[index].model_copy(update={"stated_count": stated + 1})
    rounds = (*pattern.rounds[:index], shifted, *pattern.rounds[index + 1 :])

    findings = verify(pattern.model_copy(update={"rounds": rounds}))

    assert findings == [
        Finding(
            status=FindingStatus.ERROR,
            code=FindingCode.COUNT_MISMATCH,
            round=shifted.last,
            expected=stated,
            actual=stated + 1,
        )
    ]
