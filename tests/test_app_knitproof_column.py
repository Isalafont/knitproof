"""Le passage « knitproof » : lecture par le modèle, montage par le moteur (CLA-200)."""

import datetime
import itertools
from collections.abc import Sequence
from decimal import Decimal
from importlib.resources import files

import pytest
from pydantic import SecretStr
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from knitproof.app.baseline import Verdict
from knitproof.app.beanie_reading import BeanieReading
from knitproof.app.eval_cases import EvalCase, load_eval_sets
from knitproof.app.knitproof_column import (
    READING_PROMPT,
    KnitproofRun,
    column_result,
    knitproof_pass,
)
from knitproof.app.reading_score import FieldOutcome
from knitproof.domain.notice import NoticeCode
from knitproof.domain.provenance import SourceKind
from knitproof.llm.agents import agent_on
from knitproof.llm.config import ModelConfig

SETS = load_eval_sets(files("knitproof") / "evals" / "data")
CASES = {case.id: case for cases in SETS.values() for case in cases}
NOW = datetime.datetime(2026, 11, 23, 9, 30, tzinfo=datetime.UTC)
CONFIG = ModelConfig(
    provider="anthropic",
    model="modele-fige-1",
    api_key=SecretStr("fausse"),
    base_url=None,
    host=None,
    temperature=0,
    retries=0,
    http_retries=0,
    http_wait_s=0,
)

EXAMPLE_READING: dict[str, object] = {
    "head_circumference": {"value": 48, "unit": "cm"},
    "smaller_than_head": {"value": 5, "unit": "cm"},
    "gauge_after_blocking": {"stitches": 20, "width": {"value": 10, "unit": "cm"}},
    "edge": "rib_2x2",
}


def _agent(reply_with: dict[str, object]) -> Agent[None, BeanieReading]:
    def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(
            parts=[ToolCallPart("final_result", reply_with)],
            usage=RequestUsage(input_tokens=60, output_tokens=9),
        )

    return agent_on(FunctionModel(reply), BeanieReading, 0)


def _pass(case_id: str, reading: dict[str, object]) -> KnitproofRun:
    ticks = itertools.count()
    case: EvalCase = CASES[case_id]
    return knitproof_pass(
        CONFIG,
        _agent(reading),
        case,
        1,
        clock=lambda: next(ticks) * 0.5,
        sleep=lambda seconds: None,
        now=lambda: NOW,
    )


def test_the_prompt_is_versioned() -> None:
    assert READING_PROMPT.id == "request-reading-v1"
    assert len(READING_PROMPT.sha256) == 64


def test_the_engine_casts_on_from_the_reading() -> None:
    run = _pass("exemple-bonnet-3-ans", EXAMPLE_READING)

    assert run.stitches == 84
    assert run.verdict is Verdict.CORRECT
    assert run.finished_cm is not None
    assert run.rejection is None
    assert run.incomplete is None


def test_the_reading_carries_a_model_inference_provenance() -> None:
    run = _pass("exemple-bonnet-3-ans", EXAMPLE_READING)

    assert run.reading is not None
    provenance = run.reading.provenance
    assert provenance.kind is SourceKind.MODEL_INFERENCE
    assert provenance.extracted_by is not None
    assert provenance.extracted_by.prompt_id == READING_PROMPT.id
    assert run.run.prompt_id == READING_PROMPT.id
    assert run.run.prompt_sha256 == READING_PROMPT.sha256


def test_the_fields_are_scored_against_the_expected_reading() -> None:
    run = _pass("exemple-bonnet-3-ans", EXAMPLE_READING)
    outcomes = {line.field: line.outcome for line in run.fields}

    assert outcomes["head_circumference.value"] is FieldOutcome.EXACT
    assert outcomes["edge"] is FieldOutcome.EXACT
    assert outcomes["needle_mm"] is FieldOutcome.CORRECT_ABSTENTION
    assert outcomes["worked"] is FieldOutcome.CORRECT_ABSTENTION


def test_a_number_read_wrong_makes_a_wrong_cast_on() -> None:
    wrong = {**EXAMPLE_READING, "smaller_than_head": {"value": 15, "unit": "cm"}}

    run = _pass("exemple-bonnet-3-ans", wrong)

    assert run.verdict is Verdict.WRONG
    assert {line.field: line.outcome for line in run.fields}[
        "smaller_than_head.value"
    ] is FieldOutcome.WRONG


def test_a_json_number_for_a_needle_is_accepted() -> None:
    run = _pass("bonnet-2-ans-cotes-2-2", {**EXAMPLE_READING, "needle_mm": [4], "worked": "round"})

    assert run.rejection is None
    assert {line.field: line.outcome for line in run.fields}["needle_mm"] is FieldOutcome.EXACT


def test_no_gauge_read_is_the_engine_question_and_a_correct_abstention() -> None:
    reading: dict[str, object] = {
        "head_circumference": {"value": 54.5, "unit": "cm"},
        "smaller_than_head": {"value": 4, "unit": "cm"},
        "edge": "rib_1x1",
    }

    run = _pass("bonnet-sans-jauge-abstention", reading)

    assert run.stitches is None
    assert run.questions == ("gauge_missing",)
    assert run.verdict is Verdict.CORRECT


def test_an_unknown_blocking_alone_is_a_question_hence_an_abstention() -> None:
    reading = {
        **EXAMPLE_READING,
        "gauge_after_blocking": None,
        "gauge_unknown_blocking": {"stitches": 20, "width": {"value": 10, "unit": "cm"}},
    }

    run = _pass("exemple-bonnet-3-ans", reading)

    assert run.stitches is None
    assert run.questions == (NoticeCode.GAUGE_BLOCKING_UNKNOWN.value,)
    assert run.verdict is Verdict.ABSTENTION


def test_an_incomplete_reading_is_an_abstention_naming_the_field() -> None:
    run = _pass("exemple-bonnet-3-ans", {**EXAMPLE_READING, "edge": None})

    assert run.incomplete is not None
    assert run.incomplete.field == "edge"
    assert run.stitches is None
    assert run.verdict is Verdict.ABSTENTION


def test_a_flat_reading_is_wrong() -> None:
    run = _pass("exemple-bonnet-3-ans", {**EXAMPLE_READING, "worked": "flat"})

    assert run.stitches is None
    assert run.verdict is Verdict.WRONG


def test_a_refused_output_is_an_abstention_and_misses_every_expected_field() -> None:
    run = _pass("exemple-bonnet-3-ans", {"head_circumference": "grand"})

    assert run.reading is None
    assert run.rejection
    assert run.verdict is Verdict.ABSTENTION
    outcomes = {line.field: line.outcome for line in run.fields}
    assert outcomes["head_circumference.value"] is FieldOutcome.MISSED
    assert FieldOutcome.INVENTED not in outcomes.values()


@pytest.mark.parametrize("case_id", ["exemple-bonnet-3-ans", "bonnet-sans-jauge-abstention"])
def test_the_column_counts_runs_with_a_wilson_interval(case_id: str) -> None:
    runs = [_pass(case_id, EXAMPLE_READING)] * 2 + [_pass(case_id, {"edge": None})]

    result = column_result(runs)

    assert result.total == 3
    assert result.correct + result.wrong + result.abstentions == 3
    assert result.low <= Decimal(result.correct) / 3 <= result.high


def test_the_column_counts_fields_and_inventions() -> None:
    inventing = {**EXAMPLE_READING, "worked": "round"}
    runs = [
        _pass("exemple-bonnet-3-ans", EXAMPLE_READING),
        _pass("exemple-bonnet-3-ans", inventing),
    ]

    result = column_result(runs)

    assert result.invented == 1
    assert result.fields_expected == 16  # 8 par passage : tête 2, écart 2, jauge 3, côtes 1
    assert result.fields_exact == 16
    assert result.correct_abstentions > 0


def test_a_reading_that_misses_an_expected_field_is_counted_as_expected_not_exact() -> None:
    run = _pass("exemple-bonnet-3-ans", {**EXAMPLE_READING, "edge": None})

    result = column_result([run])

    assert result.fields_expected == 8  # tête 2, écart 2, jauge 3, côtes 1
    assert result.fields_exact == 7  # tout sauf les côtes, manquées
