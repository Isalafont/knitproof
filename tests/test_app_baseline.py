"""La jauge d’un cas d’évaluation (CLA-188)."""

from importlib.resources import files

import pytest
import yaml

from knitproof.app.baseline import resolve_gauge
from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.eval_cases import EvalDataError

_EXAMPLE = files("knitproof") / "evals" / "data" / "dev" / "exemple-bonnet-3-ans.yaml"


def _request(**changes: object) -> BeanieRequest:
    case = yaml.safe_load(_EXAMPLE.read_text(encoding="utf-8"))
    return BeanieRequest.model_validate({**case["request"], **changes})


def test_the_gauge_is_the_blocked_swatch() -> None:
    gauge = resolve_gauge(_request())
    assert gauge.stitches_per_10_cm == 20


def test_a_flat_case_is_excluded() -> None:
    with pytest.raises(EvalDataError, match="à plat"):
        resolve_gauge(_request(worked="flat"))


def test_a_case_without_a_gauge_is_refused() -> None:
    with pytest.raises(EvalDataError, match="jauge"):
        resolve_gauge(_request(swatch=None))
