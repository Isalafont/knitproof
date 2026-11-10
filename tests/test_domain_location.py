"""`SourceLocation` : au moins la page ou la ligne (CLA-64)."""

import pytest
from pydantic import ValidationError

from knitproof.domain.location import SourceLocation


def test_location_without_page_nor_line_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SourceLocation()


def test_location_with_page_and_line_is_accepted() -> None:
    location = SourceLocation(page=2, line=14)

    assert (location.page, location.line) == (2, 14)


def test_location_with_only_a_line_is_accepted() -> None:
    assert SourceLocation(line=14).page is None
