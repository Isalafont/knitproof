"""Vérifier un fichier de patron : lecture, validation, constats du moteur."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from knitproof.domain.finding import Finding
from knitproof.domain.pattern import Pattern
from knitproof.engine.verification import verify


class PatternFileError(Exception):
    """Un fichier de patron absent, illisible ou invalide."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"{path} : {reason}")
        self.path = path
        self.reason = reason


def verify_pattern(path: Path) -> list[Finding]:
    """Constats du moteur sur le patron YAML de `path`."""
    return verify(_load(path))


def _load(path: Path) -> Pattern:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise PatternFileError(path, "introuvable") from error
    except OSError as error:
        raise PatternFileError(path, f"lecture impossible ({error.strerror})") from error
    except UnicodeDecodeError as error:
        raise PatternFileError(path, "pas en UTF-8") from error
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise PatternFileError(path, f"YAML mal formé\n{error}") from error
    except RecursionError as error:
        raise PatternFileError(path, "imbrication trop profonde") from error
    try:
        return Pattern.model_validate(data)
    except ValidationError as error:
        raise PatternFileError(path, f"patron invalide\n{_condense(error, data)}") from error


def _condense(error: ValidationError, data: object) -> str:
    """Une ligne par erreur : « emplacement : raison », l’emplacement en rangs si possible."""
    lines = []
    for detail in error.errors():
        location = _location(detail["loc"], data)
        lines.append(f"{location} : {detail['msg']}" if location else detail["msg"])
    return "\n".join(lines)


def _location(loc: tuple[int | str, ...], data: object) -> str:
    """Emplacement de Pydantic, avec le préfixe `rounds.<i>` remplacé par le rang écrit."""
    raw = ".".join(str(part) for part in loc)
    match loc:
        case ("rounds", int() as index, first, *rest) if first not in ("start", "end"):
            pass
        case _:
            return raw
    label = _round_label(data, index)
    if label is None:
        return raw
    return ", ".join([label, ".".join(str(part) for part in (first, *rest))])


def _round_label(data: object, index: int) -> str | None:
    """« rang 33 » ou « rangs 10 à 20 », lus tels quels dans le fichier."""
    if not isinstance(data, dict):
        return None
    rounds = data.get("rounds")
    if not isinstance(rounds, list) or index >= len(rounds):
        return None
    entry = rounds[index]
    if not isinstance(entry, dict):
        return None
    start, end = entry.get("start"), entry.get("end")
    if not _is_int(start):
        return None
    if _is_int(end):
        return f"rangs {start} à {end}"
    return f"rang {start}"


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
