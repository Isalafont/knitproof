"""Entiers stricts du domaine : un `bool` n’est pas un nombre."""

from typing import Annotated

from pydantic import Field, Strict

StrictPositiveInt = Annotated[int, Strict(), Field(gt=0)]
StrictNonNegativeInt = Annotated[int, Strict(), Field(ge=0)]
