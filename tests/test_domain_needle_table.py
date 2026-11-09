"""Validateurs de `NeedleTableRow` (CLA-67, ADR 0021)."""

import datetime

import pytest
from pydantic import ValidationError

from knitproof.domain.needle import NeedleTableRow

ROW = {
    "id": "us-6",
    "system": "us",
    "size": "6",
    "mm": ["4", "4.25"],
    "source": {
        "kind": "reference_measurement",
        "reference": "x",
        "read_on": datetime.date(2026, 11, 2),
    },
}


def test_a_well_formed_row_is_accepted() -> None:
    assert NeedleTableRow.model_validate(ROW).size == "6"


def test_the_mm_system_has_no_table() -> None:
    with pytest.raises(ValidationError, match="pas de table"):
        NeedleTableRow.model_validate({**ROW, "system": "mm", "size": "4 mm"})


@pytest.mark.parametrize(("system", "size"), [("us", "10,5"), ("jp", "6.5"), ("uk", "abc")])
def test_a_badly_formed_size_is_refused(system: str, size: str) -> None:
    with pytest.raises(ValidationError, match="mal formée"):
        NeedleTableRow.model_validate({**ROW, "system": system, "size": size})
