"""Provenance d’une valeur de bibliothèque (CLA-67, architecture §6, ADR 0008)."""

import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StringConstraints,
    model_validator,
)

from knitproof.domain.reading import ModelReading


class SourceKind(StrEnum):
    """Les dix sortes de source ; `library` restreint celles que les données admettent."""

    USER_SWATCH = "user_swatch"
    USER_MEASUREMENT = "user_measurement"
    USER_INPUT = "user_input"
    YARN_LABEL = "yarn_label"
    RAVELRY = "ravelry"
    FIBER_LIBRARY = "fiber_library"
    REFERENCE_MEASUREMENT = "reference_measurement"
    MODEL_INFERENCE = "model_inference"
    PERSON_DECISION = "person_decision"
    ENGINE = "engine"


def _only_a_date(value: object) -> object:
    if isinstance(value, datetime.datetime) or not isinstance(value, datetime.date):
        raise ValueError("une date AAAA-MM-JJ est attendue")
    return value


class Provenance(BaseModel):
    """D’où vient une valeur : sorte, référence, date de lecture, endroit dans la source.

    `location` est un texte libre (« tableau 2, p. 3 »), distinct de `SourceLocation`
    (page et ligne d’un patron). `to_verify` marque une valeur « À VÉRIFIER ».
    `extracted_by` trace le modèle qui a lu la source ; `model_inference` l’exige.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: SourceKind
    reference: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    read_on: Annotated[datetime.date, BeforeValidator(_only_a_date)]
    location: str | None = None
    to_verify: bool = False
    extracted_by: ModelReading | None = None

    @model_validator(mode="after")
    def _a_model_inference_names_its_reading(self) -> Self:
        if self.kind is SourceKind.MODEL_INFERENCE and self.extracted_by is None:
            raise ValueError("model_inference exige extracted_by")
        return self


class SourcedEntry(BaseModel):
    """Une entrée de bibliothèque : un `id`, une source, un statut facultatif.

    `status: to_verify` du fichier devient `source.to_verify` ; l’écrire dans `source` est refusé.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[str, StringConstraints(min_length=1)]
    status: Literal["to_verify"] | None = None
    source: Provenance

    @model_validator(mode="before")
    @classmethod
    def _carry_the_status_into_the_source(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        source = data.get("source")
        if not isinstance(source, dict):
            return data
        if "to_verify" in source:
            raise ValueError("to_verify s’écrit par `status: to_verify` sur l’entrée")
        if data.get("status") == "to_verify":
            return {**data, "source": {**source, "to_verify": True}}
        return data
