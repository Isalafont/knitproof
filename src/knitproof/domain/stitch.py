"""Un point et son multiple de mailles (CLA-67, ADR 0019 §6)."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from knitproof.domain.cast_on import StitchMultiple


class StitchPattern(BaseModel):
    """Identifiant, noms et multiple du point ; la liste des points revient à un autre ticket."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[str, StringConstraints(min_length=1)]
    names: tuple[str, ...]
    multiple: StitchMultiple
