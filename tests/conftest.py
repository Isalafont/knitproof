import pytest
from pydantic_ai import models


@pytest.fixture(autouse=True)
def _block_model_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(models, "ALLOW_MODEL_REQUESTS", False)
