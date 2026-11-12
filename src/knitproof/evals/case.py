"""Un cas d’évaluation et son hachage (ADR 0032)."""

import hashlib
import json
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from knitproof.domain.measure import PlainDecimal
from knitproof.domain.yarn import Text


class InjectedError(StrEnum):
    """Les types d’erreur volontaire de `docs/evaluation.md`."""

    SIZE_CONFUSION = "size_confusion"
    UNBLOCKED_GAUGE = "unblocked_gauge"
    UNIT_MISMATCH = "unit_mismatch"
    REPEAT_NOT_FITTING = "repeat_not_fitting"
    COUNT_MISMATCH = "count_mismatch"
    MISSING_FIELD = "missing_field"
    PROMPT_INJECTION = "prompt_injection"


class BaselineExpected(BaseModel):
    """Attendu de la ligne de base : le tour fini visé, tête et aisance comprises."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_circumference_cm: PlainDecimal


class EvalCase(BaseModel):
    """Une demande, ce qu’on en attend, et l’erreur volontaire qu’elle porte."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+$")]
    input: Text
    expected: BaselineExpected
    injected_error: InjectedError | None = None
    absent_fields: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _absent_fields_are_unique(self) -> Self:
        if len(set(self.absent_fields)) != len(self.absent_fields):
            raise ValueError("absent_fields : doublon")
        return self


def case_hash(case: EvalCase) -> str:
    """SHA-256 du JSON canonique du cas validé : insensible à la mise en forme du YAML."""
    return _digest(case.model_dump(mode="json"))


def content_hash(case: EvalCase) -> str:
    """Comme `case_hash`, sans l’`id` : une copie sous un autre `id` a le même contenu."""
    return _digest(case.model_dump(mode="json", exclude={"id"}))


def _digest(dumped: dict[str, object]) -> str:
    canonical = json.dumps(dumped, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
