"""Chargeur typé de `library/data/` : un modèle d’entrée par fichier (CLA-67, architecture §4).

Le registre nomme chaque fichier et son modèle d’entrée : un fichier absent du registre est
refusé. Le format de l’enveloppe est celui de CLA-124 (`data/README.md`).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Annotated, Literal, Self, cast

import yaml
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.ease import EaseSource
from knitproof.domain.fiber import Fiber, name_key
from knitproof.domain.needle import NeedleTableRow
from knitproof.domain.provenance import SourcedEntry, SourceKind
from knitproof.domain.reference import ReferenceMeasurement

# Les sortes de source admises dans les données ; `model_inference` y est refusé (ADR 0008).
DATA_KINDS = frozenset(
    {SourceKind.REFERENCE_MEASUREMENT, SourceKind.FIBER_LIBRARY, SourceKind.PERSON_DECISION}
)

# Nom de fichier → modèle d’entrée. Un fichier ajouté à `data/` s’ajoute ici.
REGISTRY: Mapping[str, type[SourcedEntry]] = {
    "0019-calotte-du-bonnet.yaml": CrownRule,
    "0020-hauteur-finie-et-bord-replie.yaml": ReferenceMeasurement,
    "0021-table-de-reference-des-tailles-d-aiguilles.yaml": NeedleTableRow,
    "0023-longueur-des-aiguilles-circulaires-et-magic-loop.yaml": MagicLoopAdvice,
    "0024-aisance-du-bonnet.yaml": EaseSource,
    "0027-tour-de-tete-par-age-d-apres-les-patrons.yaml": ReferenceMeasurement,
    "0030-fibres.yaml": Fiber,
}


class LibraryError(Exception):
    """Un fichier de la bibliothèque est absent, hors registre, illisible ou invalide."""


def _only_an_integer(value: object) -> object:
    if type(value) is not int:
        raise ValueError("un entier nu est attendu")
    return value


class DataFile[EntryT: SourcedEntry](BaseModel):
    """L’enveloppe commune des fichiers de données (format de CLA-124)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Annotated[Literal[1], BeforeValidator(_only_an_integer)]
    decided_in: Annotated[str, StringConstraints(pattern=r"^docs/adr/[0-9]{4}-[a-z0-9-]+\.md$")]
    entries: tuple[EntryT, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _entries_are_unique_and_admitted(self) -> Self:
        seen: set[str] = set()
        for entry in self.entries:
            if entry.id in seen:
                raise ValueError(f"id en double : {entry.id}")
            seen.add(entry.id)
            if entry.source.kind not in DATA_KINDS:
                raise ValueError(f"{entry.id} : source.kind {entry.source.kind} refusé en données")
        return self


@dataclass(frozen=True)
class Library:
    """Les entrées chargées, par nom de fichier."""

    files: Mapping[str, tuple[SourcedEntry, ...]]

    def entries_of[EntryT: SourcedEntry](self, model: type[EntryT]) -> tuple[EntryT, ...]:
        """Les entrées de ce modèle, tous fichiers confondus, dans l’ordre des fichiers."""
        return tuple(
            entry
            for name in sorted(self.files)
            for entry in self.files[name]
            if isinstance(entry, model)
        )


def load_library(
    directory: Traversable | None = None,
    *,
    registry: Mapping[str, type[SourcedEntry]] = REGISTRY,
) -> Library:
    """Charge et type tous les fichiers de `directory` (par défaut `library/data/`)."""
    root = directory if directory is not None else files("knitproof.library") / "data"
    present = {item.name: item for item in root.iterdir() if item.name.endswith(".yaml")}
    for name in sorted(set(present) - set(registry)):
        raise LibraryError(f"{name} : fichier absent du registre de library/loader.py")
    for name in sorted(set(registry) - set(present)):
        raise LibraryError(f"{name} : fichier du registre absent de library/data/")
    loaded = {name: _load_file(name, present[name], registry[name]) for name in sorted(present)}
    _check_fiber_names(loaded)
    return Library(loaded)


def _check_fiber_names(loaded: Mapping[str, tuple[SourcedEntry, ...]]) -> None:
    """Un nom désigne une seule fibre, tous fichiers confondus (ADR 0030)."""
    owners: dict[str, tuple[str, str]] = {}
    for name in sorted(loaded):
        for entry in loaded[name]:
            if not isinstance(entry, Fiber):
                continue
            for fiber_name in entry.names:
                key = name_key(fiber_name)
                if key in owners and owners[key][1] != entry.id:
                    other_file, other_id = owners[key]
                    raise LibraryError(
                        f"{name}:{entry.id} : nom en double « {fiber_name} » "
                        f"avec {other_file}:{other_id}"
                    )
                owners.setdefault(key, (name, entry.id))


def _load_file(
    name: str, source: Traversable, model: type[SourcedEntry]
) -> tuple[SourcedEntry, ...]:
    try:
        raw: object = yaml.load(source.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except _DuplicateKeyError as error:
        raise LibraryError(f"{name} : clé en double {error}") from error
    except (yaml.YAMLError, ValueError) as error:
        raise LibraryError(f"{name} : YAML illisible") from error
    try:
        loaded = _envelope_of(model).model_validate(raw)
    except ValidationError as error:
        raise LibraryError("\n".join(_problems(name, raw, error))) from error
    return loaded.entries


def _envelope_of(model: type[SourcedEntry]) -> type[DataFile[SourcedEntry]]:
    # `DataFile[model]` avec une variable n’est pas un type pour mypy ; l’exécution le permet.
    return cast("type[DataFile[SourcedEntry]]", DataFile.__class_getitem__(model))


def _problems(name: str, raw: object, error: ValidationError) -> list[str]:
    return [_problem(name, raw, item["loc"], item["msg"]) for item in error.errors()]


def _problem(name: str, raw: object, loc: tuple[int | str, ...], message: str) -> str:
    entry_id = _entry_id(raw, loc)
    path = ".".join(str(part) for part in (loc[2:] if entry_id else loc))
    where = f"{name}:{entry_id}" if entry_id else name
    return f"{where} : {path} : {message}" if path else f"{where} : {message}"


def _entry_id(raw: object, loc: tuple[int | str, ...]) -> str | None:
    if len(loc) < 2 or loc[0] != "entries" or not isinstance(loc[1], int):  # noqa: PLR2004
        return None
    entries = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(entries, list) or loc[1] >= len(entries):
        return None
    entry = entries[loc[1]]
    found = entry.get("id") if isinstance(entry, dict) else None
    return found if isinstance(found, str) else f"entries[{loc[1]}]"


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
