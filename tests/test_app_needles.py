"""`describe_needle` : lignes de table, texte d’information et `warning` (CLA-67, ADR 0021)."""

import pytest

from knitproof.app.needles import describe_needle
from knitproof.domain.needle import NeedleSize, NeedleSystem
from knitproof.domain.notice import NoticeCode, NoticeStatus


def needle(system: NeedleSystem, original: str) -> NeedleSize:
    return NeedleSize(system=system, original=original)


def test_us_6_gives_both_values_and_the_source_without_a_warning() -> None:
    info = describe_needle(needle(NeedleSystem.US, "6"))

    assert info.text == "US 6 : 4 ou 4,25 mm selon le CYC, À VÉRIFIER sur l’emballage"
    assert [row.id for row in info.rows] == ["us-6"]
    assert info.notice is None


def test_a_verified_row_has_no_check_mention() -> None:
    info = describe_needle(needle(NeedleSystem.US, "8"))

    assert info.text == "US 8 : 5 mm selon le CYC"


@pytest.mark.parametrize(
    ("system", "original"),
    [(NeedleSystem.US, "37"), (NeedleSystem.JP, "42")],
)
def test_a_size_missing_from_the_table_is_accepted_with_a_warning(
    system: NeedleSystem, original: str
) -> None:
    info = describe_needle(needle(system, original))

    assert info.size.original == original
    assert info.rows == ()
    assert info.notice is not None
    assert info.notice.status is NoticeStatus.WARNING
    assert info.notice.code is NoticeCode.UNKNOWN_NEEDLE_SIZE
    assert "taille inconnue de la table" in info.notice.text
    assert original in info.notice.text


def test_the_notation_is_kept_when_the_size_is_looked_up_normalized() -> None:
    info = describe_needle(needle(NeedleSystem.US, "10½"))

    assert info.size.original == "10½"
    assert [row.id for row in info.rows] == ["us-10-1-2"]
    assert info.notice is None


def test_a_mm_size_gives_only_its_value_without_a_warning() -> None:
    info = describe_needle(needle(NeedleSystem.MM, "3,6 mm"))

    assert info.text == "3,6 mm"
    assert info.rows == ()
    assert info.notice is None


def test_a_decimal_us_size_is_unknown_to_the_table_and_warned() -> None:
    info = describe_needle(needle(NeedleSystem.US, "2.5"))

    assert info.notice is not None
