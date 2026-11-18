"""La jauge, le verdict et l’intervalle de la ligne de base (CLA-188)."""

import datetime
import hashlib
import itertools
import tempfile
from collections.abc import Mapping, Sequence
from decimal import Decimal
from fractions import Fraction
from importlib.resources import files
from pathlib import Path

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import RequestUsage

from knitproof.app.baseline import (
    BASELINE_PROMPT,
    PASSES,
    AgentFactory,
    BaselineError,
    BaselineResult,
    CastOnAnswer,
    Verdict,
    measure_baseline,
    resolve_gauge,
    run_baseline,
    score,
    wilson,
    write_result,
)
from knitproof.app.baseline_journal import JournalLine
from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.eval_cases import EvalCase, EvalDataError, Split, case_hash
from knitproof.app.model_entries import PROVIDER_NAMES
from knitproof.llm.agents import agent_on
from knitproof.llm.config import ModelConfig

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
    # Jauge 20 m pour 10 cm : le tour fini vaut stitches / 2 ;
    # tour visé 43 cm (48 cm, 5 cm en moins).
    finished = Fraction(stitches, 2)
    within = abs(finished - 43) <= 1

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


def _abstention_expected() -> EvalCase:
    """L’exemple sans échantillon ni étiquette : s’abstenir est juste."""
    case = _case()
    request = BeanieRequest.model_validate({**case.request.model_dump(mode="json"), "swatch": None})
    expected = case.expected.model_copy(update={"cast_on_stitches": None, "abstain": True})
    return case.model_copy(update={"request": request, "expected": expected})


def test_an_abstention_is_correct_when_one_is_expected() -> None:
    judged = score(_abstention_expected(), CastOnAnswer(stitches=None))

    assert judged.verdict is Verdict.CORRECT
    assert judged.finished_cm is None


@pytest.mark.parametrize("stitches", [88, 1, 0, -3])
def test_a_number_is_wrong_when_an_abstention_is_expected(stitches: int) -> None:
    judged = score(_abstention_expected(), CastOnAnswer(stitches=stitches))

    assert judged.verdict is Verdict.WRONG
    assert judged.finished_cm is None


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


_SHIPPED = files("knitproof") / "evals" / "data" / "dev"
_FOLDER = tempfile.TemporaryDirectory()


def _one_case_data() -> Path:
    """Un jeu d’un seul cas, l’exemple : la mesure ne dépend pas du nombre de cas livrés."""
    root = Path(_FOLDER.name)
    (root / "dev").mkdir()
    (root / "test").mkdir()
    example = _SHIPPED.joinpath(_EXAMPLE.name).read_text(encoding="utf-8")
    (root / "dev" / _EXAMPLE.name).write_text(example, encoding="utf-8")
    digest = case_hash(EvalCase.model_validate(yaml.safe_load(example)))
    manifest = {
        "version": 1,
        "split": "dev",
        "entries": [
            {
                "case_id": "exemple-bonnet-3-ans",
                "sha256": digest,
                "annotated_by": "Isabelle Lafont",
                "annotated_on": datetime.date(2026, 11, 17),
            }
        ],
    }
    (root / "dev" / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    empty = {"version": 1, "split": "test", "entries": []}
    (root / "test" / "manifest.yaml").write_text(yaml.safe_dump(empty), encoding="utf-8")
    return root


DATA = _one_case_data()
NOW = datetime.datetime(2026, 11, 17, 9, 30, tzinfo=datetime.UTC)
ENVIRONMENT = {
    "ANTHROPIC_API_KEY": "fausse",
    "KNITPROOF_ANTHROPIC_MODEL": "claude-sonnet-5-5-20261001",
    "KNITPROOF_ANTHROPIC_TEMPERATURE": "omit",
    "KNITPROOF_OLLAMA_MODEL": "qwen3:8b",
    "KNITPROOF_OLLAMA_BASE_URL": "http://localhost:11434/v1",
    "KNITPROOF_OLLAMA_TEMPERATURE": "0",
    "KNITPROOF_LLM_RETRIES": "0",
    "KNITPROOF_LLM_HTTP_RETRIES": "0",
    "KNITPROOF_LLM_HTTP_WAIT": "0",
}


def _answering(*replies: dict[str, object] | Exception) -> AgentFactory:
    """Une fabrique dont l’agent rend `replies` tour à tour, puis la dernière en boucle."""
    queue = list(replies)

    def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        return ModelResponse(
            parts=[ToolCallPart("final_result", item)],
            usage=RequestUsage(input_tokens=51, output_tokens=4),
        )

    return lambda config: agent_on(FunctionModel(reply), CastOnAnswer, config.retries)


def _run(
    factory: AgentFactory,
    entries: Sequence[str] = ("anthropic", "ollama"),
    environ: Mapping[str, str] = ENVIRONMENT,
) -> BaselineResult:
    ticks = itertools.count()
    return run_baseline(
        Split.DEV,
        DATA,
        entries,
        environ,
        clock=lambda: next(ticks) * 0.5,
        sleep=lambda seconds: None,
        now=lambda: NOW,
        agent_factory=factory,
    )


def test_two_providers_get_the_same_prompt_and_the_same_number_of_passes() -> None:
    result = _run(_answering({"stitches": 88}))

    assert [item.provider for item in result.providers] == ["anthropic", "ollama"]
    for item in result.providers:
        assert len(item.runs) == PASSES == 3
        assert {run.run.prompt_id for run in item.runs} == {"baseline-cast-on-v1"}
        assert {run.run.prompt_sha256 for run in item.runs} == {BASELINE_PROMPT.sha256}
        assert (item.correct, item.total) == (3, 3)


def test_a_model_that_is_always_wrong_scores_zero() -> None:
    result = _run(_answering({"stitches": 96}))

    for item in result.providers:
        assert (item.correct, item.wrong, item.abstentions, item.total) == (0, 3, 0, 3)
        assert item.low == Decimal("0.0000")


def test_a_null_answer_is_an_abstention_never_correct() -> None:
    result = _run(_answering({"stitches": None}))

    for item in result.providers:
        assert (item.correct, item.abstentions) == (0, 3)


def test_a_rejected_output_is_an_abstention_with_its_reason() -> None:
    result = _run(_answering({"stitches": "quatre-vingt-huit"}), entries=("ollama",))

    runs = result.providers[0].runs
    assert {run.verdict for run in runs} == {Verdict.ABSTENTION}
    assert all(run.answer is None and run.rejection for run in runs)
    assert all(run.run.reading is None and run.run.input_tokens is None for run in runs)


def test_the_model_run_is_complete_for_a_read_pass() -> None:
    result = _run(_answering({"stitches": 88}), entries=("anthropic",))

    first = result.providers[0].runs[0]
    assert first.run.provider == "anthropic"
    assert first.run.model == "claude-sonnet-5-5-20261001"
    assert first.run.reading is not None
    assert first.run.reading.model_version
    assert first.run.temperature is None  # « non envoyée »
    assert first.run.output_mode == "tool"
    assert (first.run.input_tokens, first.run.output_tokens) == (51, 4)
    assert first.run.latency_ms == 500
    assert first.run.at == NOW
    assert (first.verdict, first.finished_cm) == (Verdict.CORRECT, Decimal(44))


def test_the_temperature_sent_is_recorded() -> None:
    result = _run(_answering({"stitches": 88}), entries=("ollama",))

    assert result.providers[0].runs[0].run.temperature == 0.0


def test_the_prompt_hash_is_stable() -> None:
    expected = hashlib.sha256(BASELINE_PROMPT.text.encode("utf-8")).hexdigest()

    assert BASELINE_PROMPT.id == "baseline-cast-on-v1"
    assert BASELINE_PROMPT.sha256 == expected
    assert BASELINE_PROMPT.sha256 == _run(_answering({"stitches": 88})).prompt_sha256


def test_a_provider_http_error_stops_the_measure_without_a_result() -> None:
    failing = ModelHTTPError(400, "claude", body="temperature is not supported")

    with pytest.raises(BaselineError, match="anthropic"):
        _run(_answering(failing), entries=("anthropic",))


RETRYING = {**ENVIRONMENT, "KNITPROOF_LLM_HTTP_RETRIES": "2"}


def test_a_passing_429_is_retried_and_the_run_records_its_attempts() -> None:
    passing = ModelHTTPError(429, "claude", body="limite")

    result = _run(_answering(passing, {"stitches": 88}), entries=("anthropic",), environ=RETRYING)

    runs = result.providers[0].runs
    assert [run.run.attempts for run in runs] == [2] + [1] * (len(runs) - 1)
    assert runs[0].verdict == Verdict.CORRECT
    assert runs[0].run.latency_ms == 500  # le seul essai qui répond


def test_an_endless_429_stops_the_measure_naming_the_provider_and_the_attempts() -> None:
    endless = ModelHTTPError(429, "claude", body="limite")

    with pytest.raises(BaselineError, match=r"anthropic.*3 essai"):
        _run(_answering(endless), entries=("anthropic",), environ=RETRYING)


def test_a_400_is_called_once_even_with_retries_allowed() -> None:
    calls: list[int] = []

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
            calls.append(1)
            raise ModelHTTPError(400, "claude", body="refusé")

        return agent_on(FunctionModel(reply), CastOnAnswer, config.retries)

    with pytest.raises(BaselineError, match="anthropic"):
        _run(factory, entries=("anthropic",), environ=RETRYING)

    assert len(calls) == 1


def test_the_sleep_is_the_one_given_to_the_measure() -> None:
    waits: list[float] = []
    ticks = itertools.count()
    environ = {**RETRYING, "KNITPROOF_LLM_HTTP_WAIT": "1.5"}

    run_baseline(
        Split.DEV,
        DATA,
        ["anthropic"],
        environ,
        clock=lambda: next(ticks) * 0.5,
        sleep=waits.append,
        now=lambda: NOW,
        agent_factory=_answering(ModelHTTPError(503, "claude", body="x"), {"stitches": 88}),
    )

    assert waits == [1.5]


def test_the_runs_of_a_measure_before_cla_197_still_validate() -> None:
    folder = Path(__file__).resolve().parents[1] / "evals" / "results"
    paths = sorted(folder.glob("*.yaml"))

    assert len(paths) == 6
    for path in paths:
        result = BaselineResult.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        assert {run.run.attempts for item in result.providers for run in item.runs} == {None}


def test_an_unknown_provider_is_refused_with_the_known_names() -> None:
    with pytest.raises(BaselineError, match="inconnu") as info:
        _run(_answering({"stitches": 88}), entries=("gemini",))

    assert all(name in str(info.value) for name in PROVIDER_NAMES)


def test_a_missing_setting_is_named_before_any_call() -> None:
    calls: list[int] = []

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        calls.append(1)
        return _answering({"stitches": 88})(config)

    environ = {k: v for k, v in ENVIRONMENT.items() if k != "ANTHROPIC_API_KEY"}

    with pytest.raises(BaselineError, match="ANTHROPIC_API_KEY"):
        _run(factory, environ=environ)
    assert calls == []


@pytest.mark.parametrize("value", ["0.5", "1"])
def test_a_temperature_other_than_zero_is_refused(value: str) -> None:
    environ = {**ENVIRONMENT, "KNITPROOF_OLLAMA_TEMPERATURE": value}

    with pytest.raises(BaselineError, match="KNITPROOF_OLLAMA_TEMPERATURE"):
        _run(_answering({"stitches": 88}), environ=environ)


def test_an_inherited_global_temperature_other_than_zero_is_refused() -> None:
    environ = {k: v for k, v in ENVIRONMENT.items() if k != "KNITPROOF_OLLAMA_TEMPERATURE"}
    environ["KNITPROOF_LLM_TEMPERATURE"] = "0.7"

    with pytest.raises(BaselineError, match="KNITPROOF_LLM_TEMPERATURE"):
        _run(_answering({"stitches": 88}), environ=environ)


@pytest.mark.parametrize("blank", [None, ""])
def test_a_provider_without_an_explicit_temperature_is_refused(blank: str | None) -> None:
    environ = {k: v for k, v in ENVIRONMENT.items() if k != "KNITPROOF_OLLAMA_TEMPERATURE"}
    if blank is not None:
        environ["KNITPROOF_OLLAMA_TEMPERATURE"] = blank
        environ["KNITPROOF_LLM_TEMPERATURE"] = "0"

    with pytest.raises(
        BaselineError, match="KNITPROOF_OLLAMA_TEMPERATURE ou KNITPROOF_LLM_TEMPERATURE"
    ):
        _run(_answering({"stitches": 88}), environ=environ)


def test_a_global_zero_counts_as_explicit() -> None:
    environ = {k: v for k, v in ENVIRONMENT.items() if k != "KNITPROOF_OLLAMA_TEMPERATURE"}
    environ["KNITPROOF_LLM_TEMPERATURE"] = "0"

    result = _run(_answering({"stitches": 88}), entries=("ollama",), environ=environ)

    assert result.providers[0].runs[0].run.temperature == 0.0


def test_the_same_entry_twice_is_refused() -> None:
    with pytest.raises(BaselineError, match="deux fois"):
        _run(_answering({"stitches": 88}), entries=("ollama", "ollama"))


def test_the_same_resolved_model_twice_is_refused() -> None:
    with pytest.raises(BaselineError, match="deux fois"):
        _run(_answering({"stitches": 88}), entries=("ollama", "ollama:qwen3:8b"))


def test_two_models_of_one_provider_make_two_lines() -> None:
    result = _run(_answering({"stitches": 88}), entries=("ollama:qwen3:8b", "ollama:llama3.2:3b"))

    first, second = result.providers
    assert [first.runs[0].run.model, second.runs[0].run.model] == ["qwen3:8b", "llama3.2:3b"]
    assert first.runs[0].run.prompt_sha256 == second.runs[0].run.prompt_sha256
    assert first.total == second.total


def test_one_model_on_two_hosts_makes_two_lines() -> None:
    environ = {
        **ENVIRONMENT,
        "OPENROUTER_API_KEY": "fausse",
        "KNITPROOF_OPENROUTER_TEMPERATURE": "0",
    }
    seen: list[ModelConfig] = []

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        seen.append(config)
        return _answering({"stitches": 88})(config)

    result = _run(factory, entries=("openrouter:x@a", "openrouter:x@b"), environ=environ)

    assert len(result.providers) == 2
    assert [(c.model, c.host) for c in seen] == [("x", "a"), ("x", "b")]


def test_a_malformed_entry_is_refused_before_any_call() -> None:
    calls: list[int] = []

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        calls.append(1)
        return _answering({"stitches": 88})(config)

    with pytest.raises(BaselineError, match="ollama:"):
        _run(factory, entries=("anthropic", "ollama:"))
    assert calls == []


def test_a_config_error_names_the_typed_entry() -> None:
    with pytest.raises(BaselineError, match="ollama:qwen3"):
        _run(_answering({"stitches": 88}), entries=("ollama:qwen3",))


def test_no_provider_is_refused() -> None:
    with pytest.raises(BaselineError, match="au moins un"):
        _run(_answering({"stitches": 88}), entries=())


def test_a_split_without_a_case_is_refused() -> None:
    ticks = itertools.count()

    with pytest.raises(BaselineError, match="aucun cas"):
        run_baseline(
            Split.TEST,
            DATA,
            ["ollama"],
            ENVIRONMENT,
            clock=lambda: next(ticks) * 0.5,
            sleep=lambda seconds: None,
            now=lambda: NOW,
            agent_factory=_answering({"stitches": 88}),
        )


def test_each_line_records_its_model_and_host() -> None:
    environ = {
        **ENVIRONMENT,
        "OPENROUTER_API_KEY": "fausse",
        "KNITPROOF_OPENROUTER_TEMPERATURE": "0",
    }

    result = _run(
        _answering({"stitches": 88}),
        entries=("ollama:qwen3:8b", "openrouter:x@a", "openrouter:y:free@b"),
        environ=environ,
    )

    assert [(item.provider, item.model, item.host) for item in result.providers] == [
        ("ollama", "qwen3:8b", None),
        ("openrouter", "x", "a"),
        ("openrouter", "y:free", "b"),
    ]


_RESULTS = Path(__file__).parent.parent / "evals" / "results"


@pytest.mark.parametrize(
    "name",
    [
        "2026-11-17T1409-dev.yaml",
        "2026-11-17T1428-dev.yaml",
        "2026-11-17T1435-dev.yaml",
        "2026-11-17T1443-dev.yaml",
        "2026-11-17T1458-dev.yaml",
        "2026-11-17T1528-dev.yaml",
    ],
)
def test_results_written_before_cla_199_still_validate(name: str) -> None:
    text = (_RESULTS / name).read_text(encoding="utf-8")

    result = BaselineResult.model_validate(yaml.safe_load(text))

    assert result.providers


def _measure_into(
    folder: Path,
    factory: AgentFactory,
    entries: Sequence[str] = ("anthropic", "ollama"),
    environ: Mapping[str, str] = ENVIRONMENT,
    resume: Path | None = None,
) -> tuple[BaselineResult, Path]:
    ticks = itertools.count()
    return measure_baseline(
        Split.DEV,
        DATA,
        entries,
        environ,
        folder,
        clock=lambda: next(ticks) * 0.5,
        sleep=lambda seconds: None,
        now=lambda: NOW,
        resume=resume,
        agent_factory=factory,
    )


def _journal_lines(folder: Path) -> list[JournalLine]:
    (path,) = folder.glob("*.partial.jsonl")
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    return [JournalLine.model_validate_json(line) for line in lines]


def test_each_pass_is_written_with_its_reading_before_the_next_call(tmp_path: Path) -> None:
    written_at_each_call: list[int] = []
    last_readings: list[bool] = []

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
            lines = _journal_lines(tmp_path) if list(tmp_path.glob("*.partial.jsonl")) else []
            written_at_each_call.append(len(lines))
            last_readings.append(bool(lines) and lines[-1].run.run.reading is not None)
            return ModelResponse(parts=[ToolCallPart("final_result", {"stitches": 88})])

        return agent_on(FunctionModel(reply), CastOnAnswer, config.retries)

    _measure_into(tmp_path, factory)

    assert written_at_each_call == [0, 1, 2, 3, 4, 5]  # à l’appel n, n - 1 passages écrits
    assert last_readings == [False] + [True] * 5


def test_an_error_at_the_fourth_pass_leaves_three_passes_and_no_result(tmp_path: Path) -> None:
    failing = ModelHTTPError(400, "claude", body="refusé")
    ok: dict[str, object] = {"stitches": 88}

    with pytest.raises(BaselineError, match="ollama"):
        _measure_into(tmp_path, _answering(ok, ok, ok, failing))

    assert len(_journal_lines(tmp_path)) == 3
    assert list(tmp_path.glob("*.yaml")) == []


def test_a_measure_without_interruption_writes_the_same_result_and_drops_the_journal(
    tmp_path: Path,
) -> None:
    factory = _answering({"stitches": 88})

    result, written = _measure_into(tmp_path / "journal", factory)

    plain = write_result(_run(factory), tmp_path / "plain")
    assert written.name == plain.name
    assert yaml.safe_load(written.read_text(encoding="utf-8")) == yaml.safe_load(
        plain.read_text(encoding="utf-8")
    )
    assert list((tmp_path / "journal").glob("*.partial.jsonl")) == []
    assert result == _run(factory)


def test_an_existing_result_is_refused_before_any_call(tmp_path: Path) -> None:
    calls: list[int] = []
    (tmp_path / "2026-11-17T0930-dev.yaml").write_text("déjà là", encoding="utf-8")

    def factory(config: ModelConfig) -> Agent[None, CastOnAnswer]:
        def reply(messages: Sequence[ModelMessage], info: AgentInfo) -> ModelResponse:
            calls.append(1)
            return ModelResponse(parts=[ToolCallPart("final_result", {"stitches": 88})])

        return agent_on(FunctionModel(reply), CastOnAnswer, config.retries)

    with pytest.raises(BaselineError, match="existe déjà"):
        _measure_into(tmp_path, factory)

    assert calls == []
    assert list(tmp_path.glob("*.partial.jsonl")) == []


def test_an_existing_journal_is_refused_by_a_fresh_launch_naming_it(tmp_path: Path) -> None:
    journal = tmp_path / "2026-11-17T0930-dev.partial.jsonl"
    journal.write_text("restes", encoding="utf-8")

    with pytest.raises(BaselineError, match=r"partial\.jsonl.*existe déjà"):
        _measure_into(tmp_path, _answering({"stitches": 88}))

    assert journal.read_text(encoding="utf-8") == "restes"


def test_a_result_and_a_leftover_journal_tell_to_delete_the_journal(tmp_path: Path) -> None:
    (tmp_path / "2026-11-17T0930-dev.yaml").write_text("déjà là", encoding="utf-8")
    (tmp_path / "2026-11-17T0930-dev.partial.jsonl").write_text("restes", encoding="utf-8")

    with pytest.raises(BaselineError, match="supprimer le journal"):
        _measure_into(tmp_path, _answering({"stitches": 88}))
