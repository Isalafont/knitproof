"""Les données d’évaluation livrées se chargent, le moteur confirme leurs attendus (CLA-188)."""

from importlib.resources import files

import pytest

from knitproof.app.baseline import resolve_gauge
from knitproof.app.eval_cases import EvalCase, Split, load_eval_sets
from knitproof.domain.measure import LengthUnit
from knitproof.engine.cast_on import cast_on

DATA = files("knitproof") / "evals" / "data"
SETS = load_eval_sets(DATA)
CASES = [case for cases in SETS.values() for case in cases]


def test_the_shipped_data_loads() -> None:
    assert [case.id for case in SETS[Split.DEV]] == ["exemple-bonnet-3-ans"]
    assert SETS[Split.TEST] == ()


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_the_expected_target_is_the_one_of_the_request(case: EvalCase) -> None:
    target = case.request.circumference
    assert target.unit is LengthUnit.CM, case.id
    assert target.value == case.expected.target_circumference_cm, case.id


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_the_expected_cast_on_is_the_one_of_the_engine(case: EvalCase) -> None:
    result = cast_on(case.request.circumference, resolve_gauge(case.request), case.request.multiple)
    assert result.stitches == case.expected.cast_on_stitches, case.id
