"""Le chargeur type chaque fichier de `library/data/` par son modèle d’entrée (CLA-67)."""

import datetime
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pytest

from knitproof.domain.fiber import Fiber
from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.measure import PlainDecimal
from knitproof.domain.provenance import SourcedEntry, SourceKind
from knitproof.domain.yarn import Yarn
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


def test_a_reading_in_the_data_is_refused(tmp_path: Path) -> None:
    reading = (
        "      extracted_by:\n"
        "        provider: anthropic\n"
        "        model: m\n"
        "        model_version: v\n"
        "        prompt_id: p\n"
        f"        prompt_sha256: {'a' * 64}\n"
    )
    write(tmp_path, HEADER + ENTRY + reading)

    with pytest.raises(LibraryError, match=r"rows\.yaml.*a : source\.extracted_by refusé"):
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


FIBERS = """\
schema_version: 1
decided_in: docs/adr/0030-laines-de-reference.md
entries:
  - id: {first}
    names: [{first_names}]
    source:
      kind: person_decision
      reference: Isabelle Lafont, décision du 12/11/2026
      read_on: 2026-11-12
  - id: {second}
    names: [{second_names}]
    source:
      kind: person_decision
      reference: Isabelle Lafont, décision du 12/11/2026
      read_on: 2026-11-12
"""


def load_fibers(directory: Path, first_names: str, second_names: str) -> Library:
    text = FIBERS.format(
        first="wool", first_names=first_names, second="merino", second_names=second_names
    )
    write(directory, text, name="fibers.yaml")
    return load_library(directory, registry={"fibers.yaml": Fiber})


def test_a_name_shared_by_two_fibers_is_refused_with_file_and_id(tmp_path: Path) -> None:
    with pytest.raises(LibraryError, match=r"fibers\.yaml:merino .*nom en double.*wool"):
        load_fibers(tmp_path, "Laine, Uld", "uld")


def test_a_name_shared_by_two_fibers_is_compared_by_key(tmp_path: Path) -> None:
    with pytest.raises(LibraryError, match="nom en double"):
        load_fibers(tmp_path, "Mérinos", "Me\u0301rinos")


def test_distinct_names_load(tmp_path: Path) -> None:
    assert len(load_fibers(tmp_path, "Laine", "mérinos").entries_of(Fiber)) == 2


YARNS = """\
schema_version: 1
decided_in: docs/adr/0030-laines-de-reference.md
entries:
  - id: kid-silk
    brand: DROPS
    name: Kid-Silk
    composition:
      parts:
        - {fiber: wool, label_term: Laine, percent: 75}
        - {fiber: %s, label_term: Soie, percent: 25}
    superwash: null
    label: {}
%s    source:
      kind: reference_measurement
      reference: https://www.garnstudio.com/yarn.php?show=drops-kid-silk&cid=8
%s"""
READ_ON = "      read_on: 2026-11-12\n"
YARN_REGISTRY: Mapping[str, type[SourcedEntry]] = {"fibers.yaml": Fiber, "yarns.yaml": Yarn}


def load_yarns(
    directory: Path, second_fiber: str = "merino", swatches: str = "", read_on: str = READ_ON
) -> Library:
    load_fibers(directory, "Laine", "mérinos")
    write(directory, YARNS % (second_fiber, swatches, read_on), name="yarns.yaml")
    return load_library(directory, registry=YARN_REGISTRY)


def test_a_yarn_with_known_fibers_loads(tmp_path: Path) -> None:
    [yarn] = load_yarns(tmp_path).entries_of(Yarn)

    assert yarn.id == "kid-silk"
    assert yarn.swatches == ()


def test_a_yarn_citing_an_unknown_fiber_is_refused_with_file_and_id(tmp_path: Path) -> None:
    with pytest.raises(LibraryError, match=r"yarns\.yaml:kid-silk : fibre inconnue angora"):
        load_yarns(tmp_path, second_fiber="angora")


def test_a_composition_not_summing_to_100_is_refused(tmp_path: Path) -> None:
    load_fibers(tmp_path, "Laine", "mérinos")
    text = (YARNS % ("merino", "", READ_ON)).replace("percent: 25", "percent: 24")
    write(tmp_path, text, name="yarns.yaml")

    with pytest.raises(LibraryError, match=r"yarns\.yaml:kid-silk .*somme"):
        load_library(tmp_path, registry=YARN_REGISTRY)


def test_a_yarn_without_read_on_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LibraryError, match=r"yarns\.yaml:kid-silk .*read_on"):
        load_yarns(tmp_path, read_on="")


def test_a_swatch_without_source_names_file_and_id(tmp_path: Path) -> None:
    swatch = (
        "    swatches:\n"
        "      - before: {stitches: '22', width: {value: '10', unit: cm}}\n"
        "        needle: {system: mm, original: 3 mm}\n"
        "        stitch: jersey\n"
        "        knitted_on: 2026-11-13\n"
    )
    with pytest.raises(LibraryError, match=r"yarns\.yaml:kid-silk .*swatches.*source"):
        load_yarns(tmp_path, swatches=swatch)


def test_a_registry_without_fibers_or_yarns_is_not_checked(tmp_path: Path) -> None:
    write(tmp_path, HEADER + ENTRY)

    assert len(load(tmp_path).entries_of(Row)) == 1
