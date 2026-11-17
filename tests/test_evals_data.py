"""Les données d’évaluation livrées se chargent, le moteur confirme leurs attendus (CLA-188)."""

from importlib.resources import files

import pytest

from knitproof.app.baseline import CastOnAnswer, Verdict, resolve_gauge, score
from knitproof.app.eval_cases import EvalCase, Split, load_eval_sets
from knitproof.domain.notice import NoticeCode
from knitproof.engine.cast_on import cast_on
from knitproof.engine.gauge import resolve_gauge as resolve_swatch

DATA = files("knitproof") / "evals" / "data"
EXAMPLE = "exemple-bonnet-3-ans"
DEV_COUNT = 5
TEST_COUNT = 15
SETS = load_eval_sets(DATA)
CASES = [case for cases in SETS.values() for case in cases]
ANSWERED = [case for case in CASES if not case.expected.abstain]
ABSTAINING = [case for case in CASES if case.expected.abstain]


def test_the_shipped_data_loads() -> None:
    # Le compte remplace la liste d’un seul id : les données changent (CLA-188, CA3).
    real = [case for case in SETS[Split.DEV] if case.id != EXAMPLE]
    assert EXAMPLE in {case.id for case in SETS[Split.DEV]}
    assert len(real) == DEV_COUNT
    assert len(SETS[Split.TEST]) == TEST_COUNT


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_the_expected_target_is_the_one_of_the_request(case: EvalCase) -> None:
    assert case.request.circumference.in_cm == case.expected.target_circumference_cm, case.id


@pytest.mark.parametrize("case", ANSWERED, ids=lambda case: case.id)
def test_the_expected_cast_on_is_the_one_of_the_engine(case: EvalCase) -> None:
    result = cast_on(case.request.circumference, resolve_gauge(case.request), case.request.multiple)
    assert result.stitches == case.expected.cast_on_stitches, case.id


@pytest.mark.parametrize("case", ABSTAINING, ids=lambda case: case.id)
def test_the_engine_asks_for_the_gauge_and_computes_no_cast_on(case: EvalCase) -> None:
    swatch = case.request.swatch
    resolved = resolve_swatch(
        blocked=None if swatch is None else swatch.after_blocking,
        unblocked=None if swatch is None else swatch.before_blocking,
        unknown=None if swatch is None else swatch.unknown_blocking,
        label=case.request.label_gauge,
    )

    assert resolved.gauge is None, case.id
    assert [question.code for question in resolved.questions] == [NoticeCode.GAUGE_MISSING.value]
    assert case.expected.cast_on_stitches is None


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_the_expected_cast_on_is_judged_correct(case: EvalCase) -> None:
    answer = CastOnAnswer(stitches=case.expected.cast_on_stitches)

    assert score(case, answer).verdict is Verdict.CORRECT, case.id
