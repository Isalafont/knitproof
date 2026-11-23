"""La ligne de base « LLM seul » : jauge du cas, verdict et mesure (CLA-188)."""

import datetime
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal, localcontext
from importlib.resources.abc import Traversable
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelAPIError

from knitproof.app.baseline_journal import (
    CaseHash,
    EntryIdentity,
    Journal,
    JournalError,
    JournalHeader,
)
from knitproof.app.baseline_models import (
    BaselineError as BaselineError,
)
from knitproof.app.baseline_models import (
    BaselineRun as BaselineRun,
)
from knitproof.app.baseline_models import (
    CastOnAnswer as CastOnAnswer,
)
from knitproof.app.baseline_models import (
    ModelRun as ModelRun,
)
from knitproof.app.baseline_models import (
    Verdict as Verdict,
)
from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.eval_cases import EvalCase, EvalDataError, Split, case_hash, load_split
from knitproof.app.model_entries import ModelEntry, ModelEntryError, parse_entry
from knitproof.domain.measure import SwatchMeasurement
from knitproof.domain.needle import KnittingMethod
from knitproof.domain.reading import ModelReading
from knitproof.engine.cast_on import check_cast_on
from knitproof.engine.gauge import resolve_gauge as resolve_swatch
from knitproof.llm.agents import agent_for
from knitproof.llm.config import ModelConfig, load_config
from knitproof.llm.errors import (
    ExtractionRejectedError,
    LlmError,
    QuotaExhaustedError,
    TransientCallError,
)
from knitproof.llm.extract import Prompt, extract

TOLERANCE_CM = Decimal(1)
WILSON_Z = Decimal("1.96")  # 95 %
_WILSON_PRECISION = 28
PASSES = 3
BASELINE_PROMPT = Prompt(
    id="baseline-cast-on-v1",
    text=(
        "Tu aides à monter les mailles d’un bonnet tricoté en rond. Lis la demande et rends "
        "le nombre entier de mailles à monter pour que le tour fini corresponde au tour visé. "
        "Si la demande ne permet pas de le déterminer, rends null. Ne rends que cette valeur."
    ),
)
_GLOBAL_TEMPERATURE = "KNITPROOF_LLM_TEMPERATURE"

type AgentFactory = Callable[[ModelConfig], Agent[None, CastOnAnswer]]


class Judgement(BaseModel):
    """Le verdict d’une réponse et le tour fini calculé par le moteur (absent sans nombre)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    verdict: Verdict
    finished_cm: Decimal | None


def resolve_gauge(request: BeanieRequest) -> SwatchMeasurement:
    """La jauge d’un cas, par l’ordre de confiance du moteur ; un cas sans jauge est refusé.

    Un cas à plat est exclu : le montage compte alors 2 lisières (ADR 0028).
    """
    if request.worked is KnittingMethod.FLAT:
        raise EvalDataError("cas à plat exclu de la ligne de base : 2 lisières en plus")
    swatch = request.swatch
    resolved = resolve_swatch(
        blocked=None if swatch is None else swatch.after_blocking,
        unblocked=None if swatch is None else swatch.before_blocking,
        unknown=None if swatch is None else swatch.unknown_blocking,
        label=request.label_gauge,
    )
    if resolved.gauge is None:
        raise EvalDataError("cas sans jauge résolue")
    return resolved.gauge


def score(case: EvalCase, answer: CastOnAnswer) -> Judgement:
    """Juste si le tour fini du montage rendu tombe à ±1 cm du tour visé, d’après le moteur.

    Pour une abstention attendue, seule l’abstention est juste. Un nombre ≤ 0 est faux sans
    tour fini : le moteur n’accepte que des entiers positifs.
    """
    stitches = answer.stitches
    if case.expected.abstain:
        # Sans jauge, aucun montage n’est calculable : s’abstenir est juste, un nombre est inventé.
        right = Verdict.CORRECT if stitches is None else Verdict.WRONG
        return Judgement(verdict=right, finished_cm=None)
    if stitches is None:
        return Judgement(verdict=Verdict.ABSTENTION, finished_cm=None)
    if stitches <= 0:
        return Judgement(verdict=Verdict.WRONG, finished_cm=None)
    request = case.request
    target = request.circumference
    check = check_cast_on(stitches, target, resolve_gauge(request), request.multiple)
    finished = check.proposed_finished_cm
    close = abs(finished - target.in_cm) <= TOLERANCE_CM
    return Judgement(verdict=Verdict.CORRECT if close else Verdict.WRONG, finished_cm=finished)


def wilson(successes: int, trials: int) -> tuple[Decimal, Decimal]:
    """Intervalle de Wilson à 95 % de `successes` sur `trials`, borné à [0, 1]."""
    if trials < 1:
        raise ValueError("wilson : au moins un essai")
    with localcontext() as context:
        context.prec = _WILSON_PRECISION
        n = Decimal(trials)
        rate = Decimal(successes) / n
        z2 = WILSON_Z * WILSON_Z
        denominator = 1 + z2 / n
        center = (rate + z2 / (2 * n)) / denominator
        half = WILSON_Z * (rate * (1 - rate) / n + z2 / (4 * n * n)).sqrt() / denominator
        low = max(Decimal(0), min(center - half, rate))
        high = min(Decimal(1), max(center + half, rate))
    return low, high


class ProviderResult(BaseModel):
    """k/N d’une entrée sur cas et passages, avec l’intervalle de Wilson à 95 %.

    `model` et `host` (hébergeur demandé) sont absents des résultats d’avant CLA-199.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    model: str | None = None
    host: str | None = None
    correct: int
    wrong: int
    abstentions: int
    total: int
    low: Decimal
    high: Decimal
    runs: tuple[BaselineRun, ...]


class BaselineResult(BaseModel):
    """La mesure d’un split : prompt figé, passages, un résultat par fournisseur."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    split: Split
    prompt_id: str
    prompt_sha256: str
    passes: int
    measured_on: datetime.datetime
    providers: tuple[ProviderResult, ...]


def build_agent(config: ModelConfig) -> Agent[None, CastOnAnswer]:
    """L’agent réel du fournisseur ; les tests remplacent cette fabrique."""
    return agent_for(config, CastOnAnswer)


def run_baseline(
    split: Split,
    data: Traversable,
    entries: Sequence[str],
    environ: Mapping[str, str],
    *,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    now: Callable[[], datetime.datetime],
    agent_factory: AgentFactory | None = None,
    journal: Journal | None = None,
    measured_on: datetime.datetime | None = None,
) -> BaselineResult:
    """Interroge chaque entrée de `--models`, `PASSES` fois par cas, et juge chaque réponse.

    Toute la configuration se valide avant le premier appel. Une erreur du fournisseur arrête
    la mesure : sans journal, aucun résultat partiel ; avec un journal, chaque passage y est
    écrit avant l’appel suivant, et les passages déjà écrits ne sont pas rappelés.
    """
    configs, cases = _prepared(split, data, entries, environ)
    return _run(
        split,
        configs,
        cases,
        clock=clock,
        sleep=sleep,
        now=now,
        agent_factory=agent_factory,
        journal=journal,
        measured_on=measured_on,
    )


def measure_baseline(
    split: Split,
    data: Traversable,
    entries: Sequence[str],
    environ: Mapping[str, str],
    results: Path,
    *,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    now: Callable[[], datetime.datetime],
    resume: Path | None = None,
    agent_factory: AgentFactory | None = None,
) -> tuple[BaselineResult, Path]:
    """La mesure complète : journal, reprise, YAML daté, puis suppression du journal.

    `resume` rouvre le journal d’une mesure interrompue : `measured_on` et le nom du YAML sont
    ceux du premier lancement. Le YAML daté se vérifie absent avant tout appel.
    """
    configs, cases = _prepared(split, data, entries, environ)
    try:
        started = Journal.read_header(resume).measured_on if resume else now()
        target = _result_path(started, split, results)
        journal_path = target.with_suffix(".partial.jsonl")
        if target.exists():
            hint = f" ; supprimer le journal {journal_path}" if journal_path.exists() else ""
            raise BaselineError(f"{target} : existe déjà, rien n’est écrasé{hint}")
        header = JournalHeader(
            split=split,
            prompt_sha256=BASELINE_PROMPT.sha256,
            passes=PASSES,
            measured_on=started,
            cases=tuple(CaseHash(case_id=case.id, sha256=case_hash(case)) for case in cases),
            entries=tuple(_identity(config) for config in configs),
        )
        journal = Journal.resume(resume, header) if resume else Journal.start(journal_path, header)
    except JournalError as error:
        raise BaselineError(str(error)) from error
    try:
        result = _run(
            split,
            configs,
            cases,
            clock=clock,
            sleep=sleep,
            now=now,
            agent_factory=agent_factory,
            journal=journal,
            measured_on=started,
        )
    except BaselineError as error:
        if journal.path.exists():
            raise BaselineError(f"{error}\nreprise : --resume {journal.path}") from error
        raise
    written = write_result(result, results)
    journal.discard()
    return result, written


def _run(
    split: Split,
    configs: Sequence[ModelConfig],
    cases: Sequence[EvalCase],
    *,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    now: Callable[[], datetime.datetime],
    agent_factory: AgentFactory | None,
    journal: Journal | None,
    measured_on: datetime.datetime | None,
) -> BaselineResult:
    factory = agent_factory or build_agent
    started = measured_on or now()
    results = tuple(
        _measure(config, factory(config), cases, clock, sleep, now, journal) for config in configs
    )
    return BaselineResult(
        split=split,
        prompt_id=BASELINE_PROMPT.id,
        prompt_sha256=BASELINE_PROMPT.sha256,
        passes=PASSES,
        measured_on=started,
        providers=results,
    )


def write_result(result: BaselineResult, folder: Path) -> Path:
    """Écrit le YAML daté `AAAA-MM-JJTHHMM-<split>.yaml` ; refuse d’écraser un fichier."""
    path = _result_path(result.measured_on, result.split, folder)
    folder.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        result.model_dump(mode="json"), allow_unicode=True, sort_keys=False, width=100
    )
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError as error:
        raise BaselineError(f"{path} : existe déjà, rien n’est écrasé") from error
    return path


def _result_path(measured_on: datetime.datetime, split: Split, folder: Path) -> Path:
    stamp = measured_on.strftime("%Y-%m-%dT%H%M")
    return folder / f"{stamp}-{split.value}.yaml"


def _prepared(
    split: Split, data: Traversable, entries: Sequence[str], environ: Mapping[str, str]
) -> tuple[list[ModelConfig], tuple[EvalCase, ...]]:
    configs = _resolved(entries, environ)
    try:
        cases = load_split(split, data)
    except EvalDataError as error:
        raise BaselineError(str(error)) from error
    if not cases:
        raise BaselineError(f"le split « {split.value} » ne contient aucun cas")
    return configs, cases


def _identity(config: ModelConfig) -> EntryIdentity:
    return EntryIdentity(provider=config.provider, model=config.model, host=config.host)


def _resolved(entries: Sequence[str], environ: Mapping[str, str]) -> list[ModelConfig]:
    """Une configuration par entrée ; deux entrées de même fournisseur, modèle et hébergeur
    résolus sont un doublon, même écrites autrement."""
    if not entries:
        raise BaselineError("au moins une entrée est attendue")
    configs: list[ModelConfig] = []
    seen: set[tuple[str, str, str | None]] = set()
    for text in entries:
        try:
            entry = parse_entry(text)
        except ModelEntryError as error:
            raise BaselineError(str(error)) from error
        config = _config_of(entry, environ)
        identity = (config.provider, config.model, config.host)
        if identity in seen:
            raise BaselineError(
                f"entrée « {text} » : même fournisseur, modèle et hébergeur nommés deux fois"
            )
        seen.add(identity)
        configs.append(config)
    return configs


def _config_of(entry: ModelEntry, environ: Mapping[str, str]) -> ModelConfig:
    """La configuration de l’entrée, avec une température explicite : 0 ou `omit`."""
    name = entry.provider
    try:
        config = load_config(name, environ, model=entry.model, host=entry.host)
    except LlmError as error:
        raise BaselineError(f"entrée « {entry.text} » : {error}") from error
    own = f"KNITPROOF_{name.upper()}_TEMPERATURE"
    variable = own if own in environ else _GLOBAL_TEMPERATURE
    if not environ.get(variable, "").strip():
        raise BaselineError(
            f"{own} ou {_GLOBAL_TEMPERATURE} : température explicite exigée, 0 ou omit"
        )
    if config.temperature not in (None, 0.0):
        raise BaselineError(f"{variable} : la ligne de base se mesure à température 0")
    return config


def _measure(
    config: ModelConfig,
    agent: Agent[None, CastOnAnswer],
    cases: Sequence[EvalCase],
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    now: Callable[[], datetime.datetime],
    journal: Journal | None,
) -> ProviderResult:
    identity = _identity(config)
    runs: list[BaselineRun] = []
    for case in cases:
        for attempt in range(1, PASSES + 1):
            kept = journal.recorded(identity, case.id, attempt) if journal else None
            if kept is None:
                kept = _pass(config, agent, case, attempt, clock, sleep, now)
                if journal:
                    journal.record(identity, kept)
            runs.append(kept)
    verdicts = [run.verdict for run in runs]
    correct = verdicts.count(Verdict.CORRECT)
    low, high = wilson(correct, len(runs))
    precision = Decimal("0.0001")
    return ProviderResult(
        provider=config.provider,
        model=config.model,
        host=config.host,
        correct=correct,
        wrong=verdicts.count(Verdict.WRONG),
        abstentions=verdicts.count(Verdict.ABSTENTION),
        total=len(runs),
        low=low.quantize(precision),
        high=high.quantize(precision),
        runs=tuple(runs),
    )


def _pass(
    config: ModelConfig,
    agent: Agent[None, CastOnAnswer],
    case: EvalCase,
    attempt: int,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    now: Callable[[], datetime.datetime],
) -> BaselineRun:
    answer: CastOnAnswer | None = None
    rejection: str | None = None
    reading: ModelReading | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    attempts: int
    try:
        extraction = extract(agent, config, BASELINE_PROMPT, case.input, clock=clock, sleep=sleep)
    except ExtractionRejectedError as error:
        rejection = str(error)
        latency_ms = error.latency_ms
        attempts = error.attempts
    except (TransientCallError, QuotaExhaustedError) as error:
        raise BaselineError(f"{config.provider} : {error}") from error
    except ModelAPIError as error:
        raise BaselineError(f"{config.provider} : {error}") from error
    else:
        answer = extraction.value
        reading = extraction.reading
        input_tokens = extraction.usage.input_tokens
        output_tokens = extraction.usage.output_tokens
        latency_ms = extraction.latency_ms
        attempts = extraction.attempts
    judged = (
        score(case, answer)
        if answer is not None
        else Judgement(verdict=Verdict.ABSTENTION, finished_cm=None)
    )
    model_run = ModelRun(
        provider=config.provider,
        model=config.model,
        prompt_id=BASELINE_PROMPT.id,
        prompt_sha256=BASELINE_PROMPT.sha256,
        reading=reading,
        temperature=config.temperature,
        output_mode="tool",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        attempts=attempts,
        at=now(),
    )
    return BaselineRun(
        case_id=case.id,
        attempt=attempt,
        answer=answer,
        rejection=rejection,
        finished_cm=judged.finished_cm,
        verdict=judged.verdict,
        run=model_run,
    )
