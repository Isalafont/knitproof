"""Le chargeur type chaque fichier de `library/data/` par son modèle d’entrée (CLA-67)."""

import datetime
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pytest

from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.measure import PlainDecimal
from knitproof.domain.provenance import SourcedEntry, SourceKind
from knitproof.library.loader import REGISTRY, DataFile, Library, LibraryError, load_library

DATA_DIR = Path(__file__).resolve().parents[1] / "src" / "knitproof" / "library" / "data"
HEADER = """\
schema_version: 1
decided_in: docs/adr/0001-verifier-les-types-avec-mypy-strict.md
entries:
"""
ENTRY = """\
  - id: a
    width: "50.5"
    count: 3
    source:
      kind: reference_measurement
      reference: Auteur, titre
      read_on: 2026-11-09
"""


class Row(SourcedEntry):
    width: PlainDecimal
    count: StrictPositiveInt


REGISTRY_OF_TESTS: Mapping[str, type[SourcedEntry]] = {"rows.yaml": Row}


def write(directory: Path, text: str, name: str = "rows.yaml") -> None:
    (directory / name).write_text(text, encoding="utf-8")


def load(directory: Path) -> Library:
    return load_library(directory, registry=REGISTRY_OF_TESTS)


def test_a_valid_file_is_loaded_with_typed_entries(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY)

    [row] = load(tmp_path).entries_of(Row)

    assert row.id == "a"
    assert row.width == Decimal("50.5")
    assert row.count == 3
    assert row.source.kind is SourceKind.REFERENCE_MEASUREMENT
    assert row.source.read_on == datetime.date(2026, 11, 9)
    assert row.source.to_verify is False


def test_an_entry_without_source_names_file_and_id(tmp_path: Path) -> None:
    text = HEADER + ENTRY.split("    source:")[0]
    write(tmp_path, text)

    with pytest.raises(LibraryError, match=r"rows\.yaml:a .*source"):
        load(tmp_path)


def test_a_file_outside_the_registry_is_refused(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY)
    write(tmp_path, HEADER + ENTRY, name="other.yaml")

    with pytest.raises(LibraryError, match=r"other\.yaml.*registre"):
        load(tmp_path)


def test_a_registered_file_that_is_missing_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LibraryError, match=r"rows\.yaml.*absent"):
        load(tmp_path)


@pytest.mark.parametrize("value", ["true", "1.5", '"abc"', '"1e3"', '"1,5"', '""', "0", '"-2"'])
def test_a_width_that_is_not_a_plain_positive_decimal_is_refused(
    tmp_path: Path, value: str
) -> None:
    write(tmp_path, HEADER + ENTRY.replace('"50.5"', value))

    with pytest.raises(LibraryError, match=r"rows\.yaml:a .*width"):
        load(tmp_path)


@pytest.mark.parametrize(("value", "expected"), [('"50.5"', "50.5"), ("50", "50"), ('"3"', "3")])
def test_a_plain_decimal_or_integer_is_accepted(tmp_path: Path, value: str, expected: str) -> None:
    write(tmp_path, HEADER + ENTRY.replace('"50.5"', value))

    [row] = load(tmp_path).entries_of(Row)

    assert row.width == Decimal(expected)


@pytest.mark.parametrize("count", ["true", "3.0", '"3"', "0"])
def test_a_count_that_is_not_a_positive_integer_is_refused(tmp_path: Path, count: str) -> None:
    write(tmp_path, HEADER + ENTRY.replace("count: 3", f"count: {count}"))

    with pytest.raises(LibraryError, match=r"rows\.yaml:a .*count"):
        load(tmp_path)


@pytest.mark.parametrize("version", ["2", "1.0", "true", '"1"'])
def test_the_schema_version_must_be_the_integer_one(tmp_path: Path, version: str) -> None:
    write(tmp_path, (HEADER + ENTRY).replace("schema_version: 1", f"schema_version: {version}"))

    with pytest.raises(LibraryError, match=r"rows\.yaml.*schema_version"):
        load(tmp_path)


def test_decided_in_must_be_an_adr_path(tmp_path: Path) -> None:
    write(tmp_path, (HEADER + ENTRY).replace("docs/adr/0001-", "notes/0001-"))

    with pytest.raises(LibraryError, match=r"rows\.yaml.*decided_in"):
        load(tmp_path)


def test_an_unknown_key_is_refused(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY + "    colour: red\n")

    with pytest.raises(LibraryError, match=r"rows\.yaml:a .*colour"):
        load(tmp_path)


def test_empty_entries_are_refused(tmp_path: Path) -> None:
    write(tmp_path, HEADER.replace("entries:\n", "entries: []\n"))

    with pytest.raises(LibraryError, match=r"rows\.yaml.*entries"):
        load(tmp_path)


def test_a_duplicate_id_is_refused(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY + ENTRY)

    with pytest.raises(LibraryError, match=r"rows\.yaml.*id en double"):
        load(tmp_path)


def test_a_duplicate_key_is_refused(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY.replace("    count: 3\n", "    count: 3\n    count: 4\n"))

    with pytest.raises(LibraryError, match=r"rows\.yaml.*clé en double"):
        load(tmp_path)


def test_an_unreadable_yaml_names_its_file(tmp_path: Path) -> None:
    write(tmp_path, "entries: [\n")

    with pytest.raises(LibraryError, match=r"rows\.yaml.*illisible"):
        load(tmp_path)


def test_a_model_inference_source_is_refused_in_the_data(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY.replace("reference_measurement", "model_inference"))

    with pytest.raises(LibraryError, match=r"rows\.yaml.*model_inference"):
        load(tmp_path)


def test_a_person_decision_source_is_admitted(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY.replace("reference_measurement", "person_decision"))

    [row] = load(tmp_path).entries_of(Row)

    assert row.source.kind is SourceKind.PERSON_DECISION


def test_a_to_verify_status_gives_a_provenance_to_verify(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY.replace("    source:", "    status: to_verify\n    source:"))

    [row] = load(tmp_path).entries_of(Row)

    assert row.source.to_verify is True


def test_two_loads_of_the_same_directory_give_the_same_result(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY)

    assert load(tmp_path) == load(tmp_path)


def test_the_data_file_envelope_is_generic_and_frozen() -> None:
    data_file = DataFile[Row].model_validate(
        {
            "schema_version": 1,
            "decided_in": "docs/adr/0001-verifier-les-types-avec-mypy-strict.md",
            "entries": [
                {
                    "id": "a",
                    "width": "1",
                    "count": 1,
                    "source": {
                        "kind": "fiber_library",
                        "reference": "x",
                        "read_on": datetime.date(2026, 11, 9),
                    },
                }
            ],
        }
    )

    assert data_file.entries[0].width == Decimal(1)


def test_every_real_data_file_is_in_the_registry_and_loads() -> None:
    names = {path.name for path in DATA_DIR.glob("*.yaml")}

    assert names == set(REGISTRY)
    assert set(load_library().files) == names
