"""Fichiers de saisie : lecture, validation et messages d’erreur en français (CLA-108, CLA-76)."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

_VALUE_ERROR_PREFIX = "Value error, "
_SHORT_COLLECTIONS = {"rounds": "au moins un rang", "ops": "au moins une opération"}


class InputFileError(Exception):
    """Un fichier de saisie absent, illisible ou invalide."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"{path} : {reason}")
        self.path = path
        self.reason = reason


def load_model[ModelT: BaseModel](path: Path, model: type[ModelT], invalid: str) -> ModelT:
    """Lit `path` en YAML et le valide ; `invalid` titre l’erreur de validation."""
    data = load_yaml(path)
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise InputFileError(path, f"{invalid}\n{condense(error, data)}") from error


def load_yaml(path: Path) -> object:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise InputFileError(path, "introuvable") from error
    except OSError as error:
        raise InputFileError(path, f"lecture impossible ({error.strerror})") from error
    except UnicodeDecodeError as error:
        raise InputFileError(path, "pas en UTF-8") from error
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise InputFileError(path, f"YAML mal formé\n{error}") from error
    except RecursionError as error:
        raise InputFileError(path, "imbrication trop profonde") from error


def condense(error: ValidationError, data: object) -> str:
    """Une ligne par erreur : « emplacement : raison », l’emplacement en rangs si possible."""
    lines = []
    for detail in error.errors():
        location = _location(detail["loc"], data)
        reason = _reason(detail["type"], detail["msg"], detail["loc"], detail.get("ctx") or {})
        lines.append(f"{location} : {reason}" if location else reason)
    return "\n".join(lines)


def _reason(kind: str, message: str, loc: tuple[int | str, ...], context: dict[str, object]) -> str:
    match kind:
        case "greater_than":
            return f"doit être supérieur à {context['gt']}"
        case "greater_than_equal":
            return f"doit valoir au moins {context['ge']}"
        case "too_short":
            return _SHORT_COLLECTIONS.get(str(loc[-1]) if loc else "", "trop court")
        case "extra_forbidden":
            return "clé inconnue"
        case "missing":
            return "champ obligatoire"
        case "int_type" | "int_parsing":
            return "un entier est attendu"
        case "union_tag_invalid" | "union_tag_not_found":
            return "forme non reconnue"
        case "decimal_max_digits":
            return "nombre trop grand ou trop précis"
        case "value_error":
            return message.removeprefix(_VALUE_ERROR_PREFIX)
        case _:
            return message


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
