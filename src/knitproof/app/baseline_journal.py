"""Le journal JSON Lines d’une mesure : un passage par ligne, reprise après arrêt (CLA-203).

La première ligne est l’en-tête de la mesure, chaque ligne suivante un passage. Le journal naît
au premier passage enregistré ; chaque ligne est vidée sur disque avant l’appel suivant.
"""

import datetime
import os
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationError

from knitproof.app.baseline_models import BaselineRun
from knitproof.app.eval_cases import Split


class JournalError(Exception):
    """Le journal est absent, illisible, déjà là, ou ne correspond pas à la mesure demandée."""


class EntryIdentity(BaseModel):
    """Une entrée de `--models` résolue : fournisseur, modèle, hébergeur demandé."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    model: str
    host: str | None


class CaseHash(BaseModel):
    """Le hachage d’un cas au moment de la mesure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str
    sha256: str


class JournalHeader(BaseModel):
    """Ce qui fait une mesure : split, prompt, passages, cas et entrées résolues."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    split: Split
    prompt_sha256: str
    passes: int
    measured_on: datetime.datetime
    cases: tuple[CaseHash, ...]
    entries: tuple[EntryIdentity, ...]


class JournalLine(BaseModel):
    """Un passage enregistré, avec l’entrée qui l’a produit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity: EntryIdentity
    run: BaselineRun


_SHOWN_MAX = 80
type _Key = tuple[EntryIdentity, str, int]


class Journal:
    """Le fichier de passages d’une mesure."""

    def __init__(self, path: Path, header: JournalHeader, known: dict[_Key, BaselineRun]) -> None:
        self._path = path
        self._header = header
        self._known = known
        self._born = bool(known) or path.exists()

    @classmethod
    def start(cls, path: Path, header: JournalHeader) -> Self:
        """Un journal neuf ; le fichier naît au premier `record`. Refuse un journal existant."""
        if path.exists():
            raise JournalError(f"{path} : le journal existe déjà, rien n’est écrasé")
        return cls(path, header, {})

    @classmethod
    def resume(cls, path: Path, expected: JournalHeader) -> Self:
        """Rouvre un journal pour le même `expected` ; coupe une ligne finale inachevée."""
        header, known, valid_size = cls._read(path)
        for name in JournalHeader.model_fields:
            if name == "measured_on":
                continue
            if getattr(header, name) != getattr(expected, name):
                raise JournalError(
                    f"{path} : journal d’une autre mesure, « {name} » diffère "
                    f"(journal : {_shown(getattr(header, name))} ; demandé : "
                    f"{_shown(getattr(expected, name))})"
                )
        os.truncate(path, valid_size)
        return cls(path, header, known)

    @classmethod
    def read_header(cls, path: Path) -> JournalHeader:
        """L’en-tête d’un journal, pour reprendre la date du premier lancement."""
        return cls._read(path)[0]

    def recorded(self, identity: EntryIdentity, case_id: str, attempt: int) -> BaselineRun | None:
        """Le passage déjà enregistré, ou `None`."""
        return self._known.get((identity, case_id, attempt))

    def record(self, identity: EntryIdentity, run: BaselineRun) -> None:
        """Ajoute le passage et le vide sur disque avant de rendre la main."""
        line = JournalLine(identity=identity, run=run)
        text = line.model_dump_json() + "\n"
        if not self._born:
            text = self._header.model_dump_json() + "\n" + text
        mode = "a" if self._born else "x"
        try:
            with self._path.open(mode, encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as error:
            raise JournalError(f"{self._path} : le journal existe déjà") from error
        self._born = True
        self._known[(identity, run.case_id, run.attempt)] = run

    def discard(self) -> None:
        """Supprime le journal, une fois le résultat daté écrit."""
        self._path.unlink(missing_ok=True)

    @staticmethod
    def _read(path: Path) -> tuple[JournalHeader, dict[_Key, BaselineRun], int]:
        try:
            data = path.read_bytes()
        except FileNotFoundError as error:
            raise JournalError(f"{path} : journal introuvable") from error
        # Sans fin de ligne, la dernière pièce est un passage coupé en pleine écriture.
        lines = data.split(b"\n")[:-1]
        try:
            header = JournalHeader.model_validate_json(lines[0])
        except (IndexError, ValidationError) as error:
            raise JournalError(f"{path} : en-tête absent ou illisible") from error
        known: dict[_Key, BaselineRun] = {}
        size = len(lines[0]) + 1
        for number, raw in enumerate(lines[1:], start=2):
            try:
                line = JournalLine.model_validate_json(raw)
            except ValidationError as error:
                if number == len(lines) and len(data) == sum(len(item) + 1 for item in lines):
                    break  # dernière ligne illisible : arrêt brutal pendant l’écriture
                raise JournalError(f"{path} : ligne {number} illisible") from error
            known[(line.identity, line.run.case_id, line.run.attempt)] = line.run
            size += len(raw) + 1
        return header, known, size


def _shown(value: object) -> str:
    text = str(value)
    return text if len(text) <= _SHOWN_MAX else text[: _SHOWN_MAX - 3] + "..."
