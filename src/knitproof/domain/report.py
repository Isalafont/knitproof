"""Rapport unique du moteur : constats, avis, contrôles (CLA-69, ADR 0029)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from knitproof.domain.beanie import BeaniePlan
from knitproof.domain.integers import StrictPositiveInt
from knitproof.domain.question import PendingQuestion


class ReportStatus(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class DecidedBy(StrEnum):
    ENGINE = "engine"
    ENTERED = "entered"
    LIBRARY = "library"

    @property
    def label(self) -> str:
        match self:
            case DecidedBy.ENGINE:
                return "le moteur (calcul vérifiable)"
            case DecidedBy.ENTERED:
                return "la valeur saisie"
            case DecidedBy.LIBRARY:
                return "la bibliothèque sourcée"


class ReportEntry(BaseModel):
    """Une ligne du rapport : statut, code, rang, texte et qui a décidé."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ReportStatus
    code: str
    round: StrictPositiveInt | None
    lines: tuple[str, ...]
    decided_by: DecidedBy


class Report(BaseModel):
    """Entrées dans l’ordre d’arrivée, questions en attente, plan s’il existe."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entries: tuple[ReportEntry, ...]
    questions: tuple[PendingQuestion, ...]
    result: BeaniePlan | None = None

    @property
    def has_errors(self) -> bool:
        return any(entry.status is ReportStatus.ERROR for entry in self.entries)

    @property
    def needs_review(self) -> bool:
        return bool(self.questions) or any(
            entry.status is ReportStatus.NEEDS_REVIEW for entry in self.entries
        )
