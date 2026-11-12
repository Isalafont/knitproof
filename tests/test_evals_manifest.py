"""Le manifeste haché vérifie chaque cas d’évaluation (CLA-126, ADR 0032)."""

import datetime
from pathlib import Path

import pytest
import yaml

from knitproof.evals.case import EvalCase, case_hash
from knitproof.evals.manifest import EvalDataError, EvalManifest, Split, load_split


def _case(case_id: str = "cas-1", target: str = "44") -> dict[str, object]:
    return {
        "id": case_id,
        "input": "Bonnet pour 3 ans.",
        "expected": {"target_circumference_cm": target},
    }


def _entry(case: dict[str, object], sha256: str | None = None) -> dict[str, object]:
    return {
        "case_id": case["id"],
        "sha256": sha256 or case_hash(EvalCase.model_validate(case)),
        "annotated_by": "Isabelle Lafont",
        "annotated_on": datetime.date(2026, 11, 12),
    }


def _write(
    root: Path,
    split: str,
    cases: list[dict[str, object]],
    entries: list[dict[str, object]] | None = None,
    manifest_split: str | None = None,
) -> None:
    folder = root / split
    folder.mkdir(parents=True, exist_ok=True)
    for case in cases:
        (folder / f"{case['id']}.yaml").write_text(
            yaml.safe_dump(case, allow_unicode=True), encoding="utf-8"
        )
    listed = entries if entries is not None else [_entry(case) for case in cases]
    manifest = {"version": 1, "split": manifest_split or split, "entries": listed}
    (folder / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
    )


def test_matching_cases_and_manifest_load(tmp_path: Path) -> None:
    _write(tmp_path, "dev", [_case("cas-1"), _case("cas-2", "45")])
    loaded = load_split(Split.DEV, tmp_path)
    assert [case.id for case in loaded] == ["cas-1", "cas-2"]


def test_a_modified_expected_value_names_the_case_and_gives_the_hash(tmp_path: Path) -> None:
    original = _case()
    _write(tmp_path, "dev", [_case(target="45")], [_entry(original)])
    obtained = case_hash(EvalCase.model_validate(_case(target="45")))
    with pytest.raises(EvalDataError) as error:
        load_split(Split.DEV, tmp_path)
    assert "cas-1" in str(error.value)
    assert obtained in str(error.value)


def test_a_case_without_an_entry_is_named(tmp_path: Path) -> None:
    _write(tmp_path, "dev", [_case("cas-1"), _case("cas-2")], [_entry(_case("cas-1"))])
    with pytest.raises(EvalDataError, match="cas-2"):
        load_split(Split.DEV, tmp_path)


def test_an_entry_without_a_case_is_named(tmp_path: Path) -> None:
    _write(tmp_path, "dev", [_case("cas-1")], [_entry(_case("cas-1")), _entry(_case("cas-9"))])
    with pytest.raises(EvalDataError, match="cas-9"):
        load_split(Split.DEV, tmp_path)


def test_a_manifest_split_different_from_its_folder_is_refused(tmp_path: Path) -> None:
    _write(tmp_path, "dev", [_case()], manifest_split="test")
    with pytest.raises(EvalDataError, match="split"):
        load_split(Split.DEV, tmp_path)


def test_a_duplicate_case_id_in_a_manifest_is_refused(tmp_path: Path) -> None:
    entry = _entry(_case())
    _write(tmp_path, "dev", [_case()], [entry, entry])
    with pytest.raises(EvalDataError, match="cas-1"):
        load_split(Split.DEV, tmp_path)


def test_an_annotation_date_given_as_text_is_refused(tmp_path: Path) -> None:
    entry = {**_entry(_case()), "annotated_on": "12 novembre"}
    _write(tmp_path, "dev", [_case()], [entry])
    folder = tmp_path / "dev"
    manifest = (folder / "manifest.yaml").read_text(encoding="utf-8")
    # `safe_dump` cite la chaîne : elle reste un texte pour le chargeur.
    assert "12 novembre" in manifest
    with pytest.raises(EvalDataError, match="annotated_on"):
        load_split(Split.DEV, tmp_path)


def test_an_unquoted_yaml_date_loads_as_a_date(tmp_path: Path) -> None:
    # Constaté par essai sur PyYAML 6.0.3 ; la doc ne cite que `datetime.datetime`.
    case = _case()
    folder = tmp_path / "dev"
    folder.mkdir()
    (folder / "cas-1.yaml").write_text(yaml.safe_dump(case), encoding="utf-8")
    digest = case_hash(EvalCase.model_validate(case))
    (folder / "manifest.yaml").write_text(
        "version: 1\nsplit: dev\nentries:\n"
        f'  - case_id: cas-1\n    sha256: "{digest}"\n'
        "    annotated_by: Isabelle Lafont\n    annotated_on: 2026-11-12\n",
        encoding="utf-8",
    )
    assert load_split(Split.DEV, tmp_path)[0].id == "cas-1"


def test_an_empty_manifest_is_allowed(tmp_path: Path) -> None:
    _write(tmp_path, "test", [])
    assert load_split(Split.TEST, tmp_path) == ()


def test_the_manifest_model_allows_no_entries() -> None:
    assert EvalManifest.model_validate({"version": 1, "split": "test", "entries": []}).entries == ()
