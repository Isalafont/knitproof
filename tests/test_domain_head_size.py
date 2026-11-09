"""Tailles nommées du tour de tête et sexe adulte (CLA-112, ADR 0026)."""

import pytest

from knitproof.domain.head_size import HeadSize, Sex

GRID = [
    "months_0_3",
    "months_6",
    "months_9",
    "months_12",
    "months_18",
    "months_24",
    "years_2_3",
    "years_4",
    "years_5_7",
    "years_7_9",
    "years_10_12",
    "years_12_14",
    "years_14_16",
    "years_17",
    "adult_s",
    "adult_m",
    "adult_l",
]


def test_the_sizes_are_the_seventeen_of_the_grid() -> None:
    assert [size.value for size in HeadSize] == GRID


@pytest.mark.parametrize("name", GRID)
def test_each_size_is_read_from_its_name(name: str) -> None:
    assert HeadSize(name).value == name


@pytest.mark.parametrize("size", list(HeadSize))
def test_only_the_adult_sizes_are_adult(size: HeadSize) -> None:
    assert size.is_adult is size.value.startswith("adult_")


def test_the_sexes_are_female_and_male() -> None:
    assert [sex.value for sex in Sex] == ["female", "male"]
