"""La jauge, le verdict et l’intervalle de la ligne de base (CLA-188)."""

from decimal import Decimal
from fractions import Fraction
from importlib.resources import files

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st

from knitproof.app.baseline import CastOnAnswer, Verdict, resolve_gauge, score, wilson
from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.eval_cases import EvalCase, EvalDataError

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


def _case() -> EvalCase:
    raw = yaml.safe_load(_EXAMPLE.read_text(encoding="utf-8"))
    return EvalCase.model_validate(raw)


def test_a_null_answer_is_an_abstention() -> None:
    judged = score(_case(), CastOnAnswer(stitches=None))

    assert judged.verdict is Verdict.ABSTENTION
    assert judged.finished_cm is None


def test_the_engine_cast_on_is_correct() -> None:
    assert score(_case(), CastOnAnswer(stitches=88)).verdict is Verdict.CORRECT


def test_a_far_off_cast_on_is_wrong() -> None:
    judged = score(_case(), CastOnAnswer(stitches=96))

    assert judged.verdict is Verdict.WRONG
    assert judged.finished_cm == Decimal(48)


@pytest.mark.parametrize("stitches", [0, -88])
def test_a_non_positive_number_is_wrong_without_a_finished_circumference(stitches: int) -> None:
    judged = score(_case(), CastOnAnswer(stitches=stitches))

    assert judged.verdict is Verdict.WRONG
    assert judged.finished_cm is None


@given(stitches=st.integers(min_value=1, max_value=400))
def test_the_verdict_is_correct_exactly_within_one_cm(stitches: int) -> None:
    # Jauge 20 m pour 10 cm : le tour fini vaut stitches / 2 ; tour visé 43,2 cm.
    finished = Fraction(stitches, 2)
    within = abs(finished - Fraction(432, 10)) <= 1

    verdict = score(_case(), CastOnAnswer(stitches=stitches)).verdict

    assert (verdict is Verdict.CORRECT) == within


@pytest.mark.parametrize("stitches", [84, 88])
def test_a_gap_of_exactly_one_cm_is_correct(stitches: int) -> None:
    # Tour visé 43 cm (48 cm, 5 cm en moins), jauge 20 m pour 10 cm : 84 m = 42 cm, 88 m = 44 cm.
    case = _case()
    ease = {"value": "-5", "unit": "cm", "provenance": "entered"}
    request = BeanieRequest.model_validate({**case.request.model_dump(mode="json"), "ease": ease})
    exact = case.model_copy(update={"request": request})

    judged = score(exact, CastOnAnswer(stitches=stitches))

    assert judged.verdict is Verdict.CORRECT
    assert judged.finished_cm is not None
    assert abs(judged.finished_cm - 43) == 1


def _rounded(bounds: tuple[Decimal, Decimal]) -> tuple[Decimal, Decimal]:
    return bounds[0].quantize(Decimal("0.0001")), bounds[1].quantize(Decimal("0.0001"))


def test_wilson_with_no_success() -> None:
    assert _rounded(wilson(0, 15)) == (Decimal("0.0000"), Decimal("0.2039"))


def test_wilson_with_every_success() -> None:
    assert _rounded(wilson(15, 15)) == (Decimal("0.7961"), Decimal("1.0000"))


def test_wilson_needs_at_least_one_trial() -> None:
    with pytest.raises(ValueError, match="au moins un essai"):
        wilson(0, 0)


@given(data=st.data())
def test_wilson_stays_in_zero_one_and_around_the_rate(data: st.DataObject) -> None:
    trials = data.draw(st.integers(min_value=1, max_value=200))
    successes = data.draw(st.integers(min_value=0, max_value=trials))

    low, high = wilson(successes, trials)

    assert 0 <= low <= Decimal(successes) / trials <= high <= 1


@given(data=st.data())
def test_wilson_grows_with_the_successes(data: st.DataObject) -> None:
    trials = data.draw(st.integers(min_value=1, max_value=200))
    successes = data.draw(st.integers(min_value=0, max_value=trials - 1))

    low, high = wilson(successes, trials)
    next_low, next_high = wilson(successes + 1, trials)

    assert low <= next_low
    assert high <= next_high
