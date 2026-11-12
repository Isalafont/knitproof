"""Les fichiers de `library/data/` sont sourcés et sans flottant nu (CLA-124)."""

import datetime
import re
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "src" / "knitproof" / "library" / "data"
SCHEMA_VERSION = 1
SOURCE_KINDS = frozenset({"reference_measurement", "fiber_library", "person_decision"})
STATUSES = frozenset({"to_verify"})
ADR_PATH = re.compile(r"docs/adr/\d{4}-[a-z0-9-]+\.md")
VALID = """\
schema_version: 1
decided_in: docs/adr/0001-verifier-les-types-avec-mypy-strict.md
entries:
  - id: oms-0-3-mois
    head_cm: "40.5"
    count: 3
    status: to_verify
    source:
      kind: reference_measurement
      reference: OMS, Head circumference-for-age
      read_on: 2026-11-09
      location: table 2
"""


def test_library_data_files_are_valid() -> None:
    problems = [problem for path in _data_files() for problem in data_problems(path)]
    if problems:
        pytest.fail("\n".join(problems), pytrace=False)


def test_data_dir_has_no_yml_file() -> None:
    assert list(DATA_DIR.glob("*.yml")) == []


def test_a_valid_file_passes(tmp_path: Path) -> None:
    path = tmp_path / "head.yaml"
    path.write_text(VALID, encoding="utf-8")
    assert data_problems(path) == []


@pytest.mark.parametrize("kind", ["reference_measurement", "fiber_library", "person_decision"])
def test_every_admitted_kind_passes(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "head.yaml"
    path.write_text(VALID.replace("kind: reference_measurement", f"kind: {kind}"), encoding="utf-8")
    assert data_problems(path) == []


@pytest.mark.parametrize(
    ("old", "new", "reason"),
    [
        ("      read_on: 2026-11-09\n", "", "read_on"),
        ("status: to_verify", "status: verified", "status"),
        ("kind: reference_measurement", "kind: model_inference", "kind"),
        ("read_on: 2026-11-09", "read_on: 9 novembre", "read_on"),
        ("schema_version: 1", "schema_version: 2", "schema_version"),
        ("0001-verifier-les-types-avec-mypy-strict", "0999-absent", "decided_in"),
        ("schema_version: 1", "schema_version: 1.0", "schema_version"),
        ("schema_version: 1", "schema_version: true", "schema_version"),
        ("schema_version: 1", "schema_version: 1\n1.5: clé", "flottant nu 1.5"),
        ("  - id: oms-0-3-mois\n", "  - nom: oms\n", "id manquant"),
        ("reference: OMS, Head circumference-for-age", "reference: ''", "reference"),
        ("location: table 2", "location: 3", "location"),
        ("read_on: 2026-11-09", "read_on: 2026-11-09 10:00:00", "read_on"),
        ("read_on: 2026-11-09", "read_on: 2026-13-45", "illisible"),
        (
            "      location: table 2\n",
            "      location: table 2\n      extracted_by: x\n",
            "extracted_by",
        ),
        (
            "      location: table 2\n",
            "      location: table 2\n  - id: oms-0-3-mois\n    source:\n"
            "      kind: fiber_library\n      reference: x\n      read_on: 2026-11-09\n",
            "id en double",
        ),
    ],
)
def test_an_invalid_entry_is_named(tmp_path: Path, old: str, new: str, reason: str) -> None:
    path = tmp_path / "head.yaml"
    path.write_text(VALID.replace(old, new), encoding="utf-8")
    problems = data_problems(path)
    assert problems
    assert any(reason in problem and problem.startswith("head.yaml") for problem in problems)


def test_empty_entries_are_named(tmp_path: Path) -> None:
    path = tmp_path / "head.yaml"
    head = VALID.split("entries:")[0]
    path.write_text(f"{head}entries: []\n", encoding="utf-8")
    assert any("entries" in problem for problem in data_problems(path))


def test_an_unreadable_yaml_names_its_file(tmp_path: Path) -> None:
    path = tmp_path / "head.yaml"
    path.write_text("entries: [\n", encoding="utf-8")
    assert data_problems(path) == ["head.yaml : YAML illisible"]


def test_a_duplicate_key_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "head.yaml"
    path.write_text(
        VALID.replace('    head_cm: "40.5"\n', '    head_cm: 40.5\n    head_cm: "40.5"\n'),
        encoding="utf-8",
    )
    problems = data_problems(path)
    assert problems
    assert all(problem.startswith("head.yaml") for problem in problems)
    assert any("clé en double" in problem for problem in problems)


def test_a_float_entry_names_its_id(tmp_path: Path) -> None:
    path = tmp_path / "head.yaml"
    path.write_text(VALID.replace('"40.5"', "40.5"), encoding="utf-8")
    assert data_problems(path) == ["head.yaml:oms-0-3-mois : flottant nu 40.5, en chaîne"]


def data_problems(path: Path) -> list[str]:
    try:
        data: object = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except _DuplicateKeyError as error:
        return [f"{path.name} : clé en double {error}"]
    except (yaml.YAMLError, ValueError):
        return [f"{path.name} : YAML illisible"]
    if not isinstance(data, dict):
        return [f"{path.name} : un mapping est attendu"]
    problems = _file_problems(path.name, data)
    problems.extend(
        f"{path.name} : flottant nu {value}, en chaîne"
        for value in _floats({key: item for key, item in data.items() if key != "entries"})
    )
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        return [*problems, f"{path.name} : entries doit être une liste non vide"]
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"{path.name}:entries[{index}]"
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            label = f"{path.name}:{entry['id']}"
            if entry["id"] in seen:
                problems.append(f"{label} : id en double")
            seen.add(entry["id"])
        problems.extend(_entry_problems(label, entry))
    return problems


def _file_problems(name: str, data: dict[object, object]) -> list[str]:
    problems: list[str] = []
    version = data.get("schema_version")
    if type(version) is not int or version != SCHEMA_VERSION:
        problems.append(f"{name} : schema_version doit valoir {SCHEMA_VERSION}")
    decided_in = data.get("decided_in")
    if not (
        isinstance(decided_in, str)
        and ADR_PATH.fullmatch(decided_in)
        and (PROJECT_ROOT / decided_in).is_file()
    ):
        problems.append(f"{name} : decided_in doit être le chemin d’un ADR existant")
    return problems


def _entry_problems(label: str, entry: object) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{label} : un mapping est attendu"]
    problems = [f"{label} : id manquant"] if not isinstance(entry.get("id"), str) else []
    problems.extend(f"{label} : flottant nu {value}, en chaîne" for value in _floats(entry))
    if "status" in entry and entry["status"] not in STATUSES:
        problems.append(f"{label} : status inconnu {entry['status']!r}, seul to_verify")
    source = entry.get("source")
    if not isinstance(source, dict):
        return [*problems, f"{label} : source manquante"]
    if source.get("kind") not in SOURCE_KINDS:
        problems.append(f"{label} : source.kind doit être l’un de {sorted(SOURCE_KINDS)}")
    if not isinstance(source.get("reference"), str) or not source["reference"].strip():
        problems.append(f"{label} : source.reference manquante")
    read_on = source.get("read_on")
    if not isinstance(read_on, datetime.date) or isinstance(read_on, datetime.datetime):
        problems.append(f"{label} : source.read_on doit être une date AAAA-MM-JJ")
    if "location" in source and not isinstance(source["location"], str):
        problems.append(f"{label} : source.location doit être un texte")
    if "extracted_by" in source:
        problems.append(f"{label} : source.extracted_by refusé en données")
    return problems


def _floats(value: object) -> list[float]:
    if isinstance(value, float):
        return [value]
    if isinstance(value, dict):
        return [found for item in [*value.keys(), *value.values()] for found in _floats(item)]
    if isinstance(value, list):
        return [found for item in value for found in _floats(item)]
    return []


def _data_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.yaml"))


class _DuplicateKeyError(Exception):
    pass


class _UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
        seen: set[object] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise _DuplicateKeyError(repr(key))
            seen.add(key)
        return super().construct_mapping(node, deep=deep)
