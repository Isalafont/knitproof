"""Les cas d’évaluation, leur hachage et leur manifeste (ADR 0032)."""

import datetime
import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum
from importlib.resources.abc import Traversable
from typing import Annotated, Self

import yaml
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    StringConstraints,
    ValidationError,
    model_serializer,
    model_validator,
)

from knitproof.app.beanie_reading import BeanieReading
from knitproof.app.beanie_request import BeanieRequest
from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.measure import PlainDecimal
from knitproof.domain.provenance import _only_a_date
from knitproof.domain.yarn import Text


class InjectedError(StrEnum):
    """Les types d’erreur volontaire de `docs/evaluation.md`."""

    SIZE_CONFUSION = "size_confusion"
    UNBLOCKED_GAUGE = "unblocked_gauge"
    UNIT_MISMATCH = "unit_mismatch"
    REPEAT_NOT_FITTING = "repeat_not_fitting"
    COUNT_MISMATCH = "count_mismatch"
    MISSING_FIELD = "missing_field"
    PROMPT_INJECTION = "prompt_injection"


class BaselineExpected(BaseModel):
    """Attendu de la ligne de base : le tour visé (tête et aisance) et le montage du moteur.

    Soit un montage, soit l’abstention : une demande sans jauge n’a pas de montage calculable,
    et seul un modèle qui s’abstient a juste.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_circumference_cm: PlainDecimal
    cast_on_stitches: StrictPositiveInt | None = None
    abstain: bool = False

    @model_validator(mode="after")
    def _a_cast_on_or_an_abstention(self) -> Self:
        if (self.cast_on_stitches is None) == (not self.abstain):
            raise ValueError("expected : un montage, ou abstain à vrai, jamais les deux ni aucun")
        return self

    @model_serializer(mode="wrap")
    def _omit_what_is_unused(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        """Un champ inutilisé sort du JSON : le hachage d’un cas à montage ne change pas."""
        data: dict[str, object] = handler(self)
        if not data.get("abstain"):
            data.pop("abstain", None)
        if data.get("cast_on_stitches") is None:
            data.pop("cast_on_stitches", None)
        return data


class EvalCase(BaseModel):
    """Une demande, ce qu’on en attend, et l’erreur volontaire qu’elle porte.

    `expected_reading` est la lecture du texte, telle qu’il la dit, signée par Isabelle (CLA-200).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+$")]
    input: Text
    request: BeanieRequest
    expected: BaselineExpected
    expected_reading: BeanieReading
    injected_error: InjectedError | None = None
    absent_fields: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _absent_fields_are_unique(self) -> Self:
        if len(set(self.absent_fields)) != len(self.absent_fields):
            raise ValueError("absent_fields : doublon")
        return self


def case_hash(case: EvalCase) -> str:
    """SHA-256 du JSON canonique du cas validé : insensible à la mise en forme du YAML."""
    return _digest(case.model_dump(mode="json"))


def content_hash(case: EvalCase) -> str:
    """Comme `case_hash`, sans l’`id` : une copie sous un autre `id` a le même contenu."""
    return _digest(case.model_dump(mode="json", exclude={"id"}))


def _digest(dumped: dict[str, object]) -> str:
    canonical = json.dumps(dumped, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


MANIFEST_NAME = "manifest.yaml"


class EvalDataError(Exception):
    """Un cas ou un manifeste d’évaluation est illisible, invalide ou ne concorde pas."""


class Split(StrEnum):
    DEV = "dev"
    TEST = "test"


class ManifestEntry(BaseModel):
    """Un cas : son hachage, qui l’a annoté et quand."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: Text
    sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    annotated_by: Text
    annotated_on: Annotated[datetime.date, BeforeValidator(_only_a_date)]


class EvalManifest(BaseModel):
    """Le manifeste d’un split ; vide permis, `case_id` uniques."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Annotated[int, Field(ge=1)]
    split: Split
    entries: tuple[ManifestEntry, ...]

    @model_validator(mode="after")
    def _case_ids_are_unique(self) -> Self:
        seen: set[str] = set()
        for entry in self.entries:
            if entry.case_id in seen:
                raise ValueError(f"case_id en double : {entry.case_id}")
            seen.add(entry.case_id)
        return self


def load_eval_sets(root: Traversable) -> Mapping[Split, tuple[EvalCase, ...]]:
    """Charge `dev` et `test` et refuse un même `id` ou un même contenu dans les deux."""
    sets = {split: load_split(split, root) for split in Split}
    dev, test = sets[Split.DEV], sets[Split.TEST]
    for case in test:
        for other in dev:
            if case.id == other.id:
                raise EvalDataError(f"{case.id} : même id dans dev et test")
            if content_hash(case) == content_hash(other):
                raise EvalDataError(
                    f"{other.id} (dev) et {case.id} (test) : même contenu sous deux id"
                )
    return sets


def load_split(split: Split, root: Traversable) -> tuple[EvalCase, ...]:
    """Charge les cas de `<root>/<split>/` et les compare au manifeste du dossier."""
    folder = root / split.value
    manifest = _load_manifest(split, folder / MANIFEST_NAME)
    sources = sorted(
        (item for item in folder.iterdir() if item.name.endswith(".yaml")),
        key=lambda item: item.name,
    )
    cases: list[EvalCase] = []
    files_of: dict[str, str] = {}
    for item in sources:
        if item.name == MANIFEST_NAME:
            continue
        case = _load_case(item)
        if case.id in files_of:
            raise EvalDataError(
                f"{split.value}/{case.id} : id en double dans {files_of[case.id]} et {item.name}"
            )
        files_of[case.id] = item.name
        cases.append(case)
    listed = {entry.case_id: entry for entry in manifest.entries}
    found = {case.id for case in cases}
    for case in cases:
        if case.id not in listed:
            raise EvalDataError(f"{split.value}/{case.id} : cas absent du manifeste")
    for case_id in listed:
        if case_id not in found:
            raise EvalDataError(f"{split.value}/{case_id} : entrée du manifeste sans cas")
    for case in cases:
        obtained = case_hash(case)
        if obtained != listed[case.id].sha256:
            raise EvalDataError(
                f"{split.value}/{case.id} : hachage différent de celui du manifeste, "
                f"obtenu {obtained}"
            )
    return tuple(cases)


def _load_manifest(split: Split, source: Traversable) -> EvalManifest:
    name = f"{split.value}/{MANIFEST_NAME}"
    raw = _read_yaml(name, source)
    try:
        manifest = EvalManifest.model_validate(raw)
    except ValidationError as error:
        raise EvalDataError(f"{name} : {_problems(error)}") from error
    if manifest.split is not split:
        raise EvalDataError(
            f"{name} : split « {manifest.split.value} » différent du dossier « {split.value} »"
        )
    return manifest


def _load_case(source: Traversable) -> EvalCase:
    raw = _read_yaml(source.name, source)
    try:
        return EvalCase.model_validate(raw)
    except ValidationError as error:
        raise EvalDataError(f"{source.name} : {_problems(error)}") from error


def _read_yaml(name: str, source: Traversable) -> object:
    try:
        return yaml.safe_load(source.read_text(encoding="utf-8"))
    except (yaml.YAMLError, ValueError) as error:
        raise EvalDataError(f"{name} : YAML illisible") from error


def _problems(error: ValidationError) -> str:
    return " ; ".join(
        f"{'.'.join(str(part) for part in item['loc'])} : {item['msg']}" for item in error.errors()
    )
