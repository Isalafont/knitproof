"""Les modèles d’un passage de la ligne de base : réponse, verdict, passage (CLA-188, CLA-203).

Séparés de `baseline.py` pour que le journal (`baseline_journal.py`) les importe sans cycle.
"""

import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from knitproof.domain.reading import ModelReading


class CastOnAnswer(BaseModel):
    """Ce que rend le modèle : un nombre de mailles à monter, ou `null` s’il s’abstient."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stitches: int | None


class Verdict(StrEnum):
    CORRECT = "correct"
    WRONG = "wrong"
    ABSTENTION = "abstention"


class BaselineError(Exception):
    """La mesure ne peut pas se faire : configuration invalide ou erreur du fournisseur."""


class ModelRun(BaseModel):
    """Un passage : qui a répondu, avec quel prompt et quels réglages (`None` : non envoyée).

    `attempts` compte les essais HTTP du passage ; `None` pour une mesure d’avant CLA-197, dont les
    réessais des SDK étaient invisibles. `latency_ms` est celle du seul essai qui a répondu.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    model: str
    prompt_id: str
    prompt_sha256: str
    reading: ModelReading | None
    temperature: float | None
    output_mode: Literal["tool"]
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    attempts: int | None = None
    at: datetime.datetime


class BaselineRun(BaseModel):
    """Un passage sur un cas : la réponse (ou le refus), le tour fini et le verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str
    attempt: int
    answer: CastOnAnswer | None
    rejection: str | None
    finished_cm: Decimal | None
    verdict: Verdict
    run: ModelRun
