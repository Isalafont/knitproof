"""La lecture juste, champ par champ, sans tolérance (CLA-200, `docs/evaluation.md`)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from knitproof.app.beanie_reading import BeanieReading, ReadGauge, ReadLength


class FieldOutcome(StrEnum):
    EXACT = "exact"
    WRONG = "wrong"
    INVENTED = "invented"
    MISSED = "missed"
    CORRECT_ABSTENTION = "correct_abstention"


class FieldScore(BaseModel):
    """Le sort d’un champ feuille de la lecture."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str
    outcome: FieldOutcome


_LENGTHS = ("head_circumference", "smaller_than_head", "finished_circumference")
_GAUGES = ("gauge_after_blocking", "gauge_before_blocking", "gauge_unknown_blocking", "label_gauge")


def score_reading(expected: BeanieReading, read: BeanieReading | None) -> tuple[FieldScore, ...]:
    """Une ligne par champ feuille ; une lecture `None` (refus) ne lit aucun champ.

    L’égalité est celle de `Decimal` (la valeur, pas son écriture) ; aucune tolérance.
    """
    wanted = _leaves(expected)
    found = _leaves(read if read is not None else BeanieReading())
    return tuple(
        FieldScore(field=name, outcome=_outcome(wanted[name], found[name])) for name in wanted
    )


def _outcome(wanted: object, found: object) -> FieldOutcome:
    if wanted is None:
        return FieldOutcome.CORRECT_ABSTENTION if found is None else FieldOutcome.INVENTED
    if found is None:
        return FieldOutcome.MISSED
    return FieldOutcome.EXACT if wanted == found else FieldOutcome.WRONG


def _leaves(reading: BeanieReading) -> dict[str, object]:
    leaves: dict[str, object] = {}
    for name in _LENGTHS:
        leaves.update(_length_leaves(name, getattr(reading, name)))
    for name in _GAUGES:
        leaves.update(_gauge_leaves(name, getattr(reading, name)))
    leaves["needle_mm"] = reading.needle_mm or None
    leaves["edge"] = reading.edge
    leaves["worked"] = reading.worked
    return leaves


def _length_leaves(name: str, length: ReadLength | None) -> dict[str, object]:
    return {
        f"{name}.value": None if length is None else length.value,
        f"{name}.unit": None if length is None else length.unit,
    }


def _gauge_leaves(name: str, gauge: ReadGauge | None) -> dict[str, object]:
    return {
        f"{name}.stitches": None if gauge is None else gauge.stitches,
        **_length_leaves(f"{name}.width", None if gauge is None else gauge.width),
    }
