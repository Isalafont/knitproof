"""Décision : le choix d’une personne devant une question en attente (CLA-206, ADR 0039)."""

import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints

from knitproof.domain.provenance import _only_a_date

_Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Decision(BaseModel):
    """Le choix d’une option d’une question, daté ; la date est celle de la personne.

    La date n’est jamais lue sur l’horloge : même entrée, même rapport (ADR 0029).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: _Text
    choice: _Text
    decided_on: Annotated[datetime.date, BeforeValidator(_only_a_date)]
    reason: str | None = None
