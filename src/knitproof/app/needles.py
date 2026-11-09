"""Texte d’information et `warning` d’une taille d’aiguille (CLA-67, ADR 0021 §3 à §6)."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from knitproof.domain.needle import NeedleSize, NeedleSystem, NeedleTableRow
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.library.loader import Library, load_library
from knitproof.library.lookup import needle_rows

_SHORT_NAMES = {"Craft Yarn Council": "le CYC"}


class NeedleInfo(BaseModel):
    """La taille telle que saisie, ses lignes de table, son texte et son avis éventuel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    size: NeedleSize
    rows: tuple[NeedleTableRow, ...]
    text: str
    notice: Notice | None = None


def describe_needle(size: NeedleSize, library: Library | None = None) -> NeedleInfo:
    """Rend les lignes de la table de la taille ; hors table, le texte est un `warning`.

    Un mm est une mesure : il rend sa valeur, sans table ni avis (décision 6). Les valeurs de la
    source sont toutes données, sans choisir (décision 4).
    """
    if size.system is NeedleSystem.MM:
        return NeedleInfo(size=size, rows=(), text=f"{_mm(size.known_mm)} mm")
    rows = needle_rows(library if library is not None else load_library(), size)
    if not rows:
        return _unknown(size)
    return NeedleInfo(size=size, rows=rows, text="\n".join(_text(row) for row in rows))


def _unknown(size: NeedleSize) -> NeedleInfo:
    label = f"{size.system.value.upper()} {size.original}"
    notice = Notice(
        status=NoticeStatus.WARNING,
        code=NoticeCode.UNKNOWN_NEEDLE_SIZE,
        text=f"taille inconnue de la table : {label}, notation conservée",
    )
    return NeedleInfo(
        size=size,
        rows=(),
        text=f"{label} : absente de la table, se fier aux mm de l’emballage",
        notice=notice,
    )


def _text(row: NeedleTableRow) -> str:
    values = " ou ".join(_mm(mm) for mm in row.mm)
    text = f"{row.system.value.upper()} {row.size} : {values} mm selon {_source_name(row)}"
    return f"{text}, À VÉRIFIER sur l’emballage" if row.source.to_verify else text


def _source_name(row: NeedleTableRow) -> str:
    name = row.source.reference.split(",")[0].strip()
    return _SHORT_NAMES.get(name, name)


def _mm(value: Decimal | None) -> str:
    return "?" if value is None else format(value, "f").replace(".", ",")
