"""Sources d’aisance : tailles avec plage de tête, montage ou tour publié (CLA-67, ADR 0024)."""

import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.ease import EaseProposal, EaseSize, EaseSource, EdgeStitch, Fit
from knitproof.domain.provenance import Provenance, SourceKind

SOURCE = {"kind": "reference_measurement", "reference": "x", "read_on": datetime.date(2026, 11, 9)}
HEAD = {"low": "47", "high": "48", "unit": "cm"}
SWATCH = {"stitches": "23", "width": {"value": "10", "unit": "cm"}}


def source(**changes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "a",
        "fit": "fitted",
        "edge": "stockinette",
        "swatch": SWATCH,
        "sizes": [{"head": HEAD, "cast_on": 92}],
        "source": SOURCE,
    }
    return {**base, **changes}


def test_a_source_with_a_cast_on_and_a_swatch_is_valid() -> None:
    found = EaseSource.model_validate(source())

    assert found.fit is Fit.FITTED
    assert found.edge is EdgeStitch.STOCKINETTE
    assert found.sizes[0].cast_on == 92


def test_a_source_with_a_published_circumference_needs_no_swatch() -> None:
    found = EaseSource.model_validate(
        source(
            swatch=None,
            sizes=[{"head": HEAD, "brim_circumference": {"value": "18", "unit": "in"}}],
        )
    )

    assert found.sizes[0].brim_circumference is not None


def test_a_cast_on_without_a_swatch_is_refused() -> None:
    with pytest.raises(ValidationError, match="swatch"):
        EaseSource.model_validate(source(swatch=None))


def test_a_size_needs_exactly_one_way_to_know_its_circumference() -> None:
    with pytest.raises(ValidationError, match="cast_on"):
        EaseSize.model_validate({"head": HEAD})
    with pytest.raises(ValidationError, match="cast_on"):
        EaseSize.model_validate(
            {"head": HEAD, "cast_on": 92, "brim_circumference": {"value": "40", "unit": "cm"}}
        )


def test_a_size_needs_both_ends_of_its_head_range() -> None:
    with pytest.raises(ValidationError, match="low"):
        EaseSize.model_validate({"head": {"high": "48", "unit": "cm"}, "cast_on": 92})


def test_a_source_needs_at_least_one_size() -> None:
    with pytest.raises(ValidationError, match="sizes"):
        EaseSource.model_validate(source(sizes=[]))


def test_a_proposal_refuses_a_float() -> None:
    provenance = Provenance(
        kind=SourceKind.REFERENCE_MEASUREMENT, reference="x", read_on=datetime.date(2026, 11, 9)
    )

    with pytest.raises(ValidationError, match="float refusé"):
        EaseProposal.model_validate(
            {
                "source_id": "a",
                "fit": "fitted",
                "edge": "stockinette",
                "proposed": -15.6,
                "low": Decimal(-16),
                "high": Decimal(-15),
                "by_size": (Decimal(-15),),
                "provenance": provenance,
            }
        )
