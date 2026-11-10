"""Plan de bonnet : hauteur résolue, questions en attente (CLA-68, ADR 0020 et 0028).

La jauge se résout selon l’ordre de confiance de l’ADR 0008 (CLA-66) ; le tour de tête,
l’âge et l’aisance arrivent explicites, leur résolution revient à un ticket de suite.
"""

from decimal import Inexact, Rounded
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.errors import InputFileError, load_model
from knitproof.app.needles import NeedleInfo, describe_needle
from knitproof.domain.beanie import BeanieReview, BeanieSpecification
from knitproof.domain.cast_on import CastOnResult, StitchMultiple
from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.gauge import GaugeSource, ResolvedGauge
from knitproof.domain.measure import Length, SwatchMeasurement
from knitproof.domain.needle import KnittingMethod
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.question import PendingQuestion
from knitproof.domain.reference import ReferenceMeasurement
from knitproof.domain.report import Report, ReportEntry
from knitproof.engine.beanie import beanie_plan
from knitproof.engine.cast_on import cast_on, check_cast_on, flat_cast_on
from knitproof.engine.gauge import gauge_differs_from_label, resolve_gauge
from knitproof.engine.needle import check_needles
from knitproof.engine.report import (
    build_report,
    from_cast_on_check,
    from_needle_check,
    from_notice,
    unblocked_swatch_notice,
)
from knitproof.library.loader import Library, load_library
from knitproof.library.lookup import rows_for_age

_INVALID_REQUEST = "demande de bonnet invalide"
_TOO_BIG = "nombre trop grand ou trop précis"


class BeanieCalc(BaseModel):
    """Ce que `knitproof calc` rend : inputs résolus, montage calculé, aiguilles, rapport.

    Sans jauge résolue, `cast_on` est absent et le rapport ne porte que des questions.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    request: BeanieRequest
    circumference: Length
    gauge: ResolvedGauge
    cast_on: CastOnResult | None
    needles: tuple[NeedleInfo, ...]
    report: Report


def calc_beanie(path: Path) -> BeanieCalc:
    """Lit la demande, calcule le plan et rassemble le rapport.

    Le montage calculé, l’alerte sur l’échantillon avant blocage, le contrôle du montage
    proposé et les aiguilles se trouvent ici ; un nombre trop grand est une erreur de saisie.
    """
    request = load_model(path, BeanieRequest, _INVALID_REQUEST)
    try:
        return _calc(request)
    except (Rounded, Inexact) as error:
        raise InputFileError(path, _TOO_BIG) from error


def _calc(request: BeanieRequest) -> BeanieCalc:
    circumference, multiple = request.circumference, request.multiple
    swatch = request.swatch
    resolved = resolve_gauge(
        blocked=None if swatch is None else swatch.after_blocking,
        unblocked=None if swatch is None else swatch.before_blocking,
        unknown=None if swatch is None else swatch.unknown_blocking,
        label=request.label_gauge,
    )
    gauge = resolved.gauge
    needles = tuple(describe_needle(needle.size) for needle in request.specification.needles)
    if gauge is None or resolved.source is None:
        return BeanieCalc(
            request=request,
            circumference=circumference,
            gauge=resolved,
            cast_on=None,
            needles=needles,
            report=build_report(_needle_entries(request, needles), resolved.questions),
        )
    before = (
        None
        if swatch is None or resolved.source is not GaugeSource.BLOCKED
        else (swatch.before_blocking)
    )
    review = plan_beanie(
        request.specification,
        circumference=circumference,
        stitch_multiple=multiple,
        gauge=gauge,
        source=resolved.source,
        before_blocking=before,
    )
    entries: list[ReportEntry] = [from_notice(notice) for notice in resolved.notices]
    if before is not None:
        unblocked = check_cast_on(
            cast_on(circumference, before, multiple).stitches, circumference, gauge, multiple
        )
        notice = unblocked_swatch_notice(unblocked, before)
        if notice is not None:
            entries.append(from_notice(notice))
    if request.label_gauge is not None and resolved.source is not GaugeSource.LABEL:
        entries.extend(from_notice(n) for n in gauge_differs_from_label(gauge, request.label_gauge))
    if request.proposed_cast_on is not None:
        proposal = request.proposed_cast_on.stitches
        rejected = from_cast_on_check(
            check_cast_on(proposal, circumference, gauge, multiple),
            gauge,
            title=f"Proposition d’un LLM seul : {proposal} m",
            source=resolved.source,
        )
        if rejected is not None:
            entries.append(rejected)
    entries.extend(from_notice(notice) for notice in review.notices)
    entries.extend(_needle_entries(request, needles))
    return BeanieCalc(
        request=request,
        circumference=circumference,
        gauge=resolved,
        cast_on=cast_on(circumference, gauge, multiple),
        needles=needles,
        report=build_report(entries, review.questions, review.plan),
    )


def _needle_entries(request: BeanieRequest, needles: tuple[NeedleInfo, ...]) -> list[ReportEntry]:
    """Les avis sur les tailles, puis le contrôle des aiguilles de l’échantillon, s’il y en a un."""
    entries = [from_notice(info.notice) for info in needles if info.notice is not None]
    if request.swatch is not None:
        for project in request.specification.needles:
            checked = from_needle_check(check_needles(request.swatch.needle, project))
            if checked is not None:
                entries.append(checked)
    return entries


def plan_beanie(
    spec: BeanieSpecification,
    *,
    circumference: Length,
    stitch_multiple: StitchMultiple,
    gauge: SwatchMeasurement,
    source: GaugeSource = GaugeSource.BLOCKED,
    before_blocking: SwatchMeasurement | None = None,
    library: Library | None = None,
) -> BeanieReview:
    """Le plan du bonnet, ou les questions qui manquent pour le calculer.

    `gauge` est la jauge résolue et `source` d’où elle vient ; `before_blocking` n’est donné
    que si l’échantillon bloqué et le non bloqué coexistent.

    La hauteur saisie prime ; sans saisie, la ligne de la table Knit Picks de l’âge, avec un
    `warning` (ADR 0020 §3 et §6). Un âge sans ligne unique donne un `needs_review`.
    """
    data = library if library is not None else load_library()
    notices: list[Notice] = []
    questions: list[PendingQuestion] = []
    height = _resolve_height(spec, data, notices, questions)
    if spec.brim_height is None:
        questions.append(
            _question(
                NoticeCode.BRIM_HEIGHT_MISSING, "Quelle est la hauteur du bord (ou du revers) ?"
            )
        )
    if gauge.rows is None:
        questions.append(_question(NoticeCode.ROW_GAUGE_MISSING, _rows_question(source)))
    if height is None or spec.brim_height is None or gauge.rows is None:
        return BeanieReview(plan=None, notices=tuple(notices), questions=tuple(questions))
    stitches = _stitches(spec, circumference, stitch_multiple, gauge)
    review = beanie_plan(
        stitches=stitches,
        worked=spec.worked,
        stitch_multiple=stitch_multiple,
        finished_height=height,
        brim_height=spec.brim_height,
        folded_brim=spec.folded_brim,
        after_blocking=gauge,
        before_blocking=before_blocking,
        needles=spec.needles,
        crown_rule=_only(data.entries_of(CrownRule)),
        advice=_only(data.entries_of(MagicLoopAdvice)),
    )
    return BeanieReview(
        plan=review.plan,
        notices=(*notices, *review.notices),
        questions=(*questions, *review.questions),
    )


def _rows_question(source: GaugeSource) -> str:
    where = {
        GaugeSource.BLOCKED: "l’échantillon, après blocage",
        GaugeSource.UNBLOCKED: "l’échantillon, avant blocage",
        GaugeSource.LABEL: "la jauge de l’étiquette",
    }[source]
    return f"Combien de rangs sur quelle hauteur dans {where} ?"


def _stitches(
    spec: BeanieSpecification,
    circumference: Length,
    stitch_multiple: StitchMultiple,
    swatch: SwatchMeasurement,
) -> int:
    if spec.worked is KnittingMethod.FLAT:
        return flat_cast_on(circumference, swatch, stitch_multiple).body.stitches
    return cast_on(circumference, swatch, stitch_multiple).stitches


def _resolve_height(
    spec: BeanieSpecification,
    library: Library,
    notices: list[Notice],
    questions: list[PendingQuestion],
) -> Length | None:
    if spec.total_height is not None:
        return spec.total_height
    rows = () if spec.age is None else rows_for_age(library, spec.age)
    if len(rows) == 1 and rows[0].value is not None:
        notices.append(_from_table(rows[0], rows[0].value.length))
        return rows[0].value.length
    text = (
        "À REVOIR : la hauteur finie n’est pas saisie et la table Knit Picks ne désigne pas "
        f"une seule ligne pour cet âge ({len(rows)} ligne(s)), aucun milieu n’est calculé"
    )
    notices.append(
        Notice(status=NoticeStatus.NEEDS_REVIEW, code=NoticeCode.HEIGHT_UNRESOLVED, text=text)
    )
    questions.append(
        _question(NoticeCode.HEIGHT_UNRESOLVED, "Quelle est la hauteur finie du bonnet ?")
    )
    return None


def _from_table(row: ReferenceMeasurement, height: Length) -> Notice:
    text = (
        f"À VÉRIFIER : hauteur finie de {format(height.value, 'f')} {height.unit.value} prise "
        f"dans la table ({row.label}), sa mesure n’est pas définie ; source : "
        f"{row.source.reference}"
    )
    return Notice(status=NoticeStatus.WARNING, code=NoticeCode.HEIGHT_FROM_TABLE, text=text)


def _question(code: NoticeCode, text: str) -> PendingQuestion:
    return PendingQuestion(code=code, text=text, options=())


def _only[EntryT](entries: tuple[EntryT, ...]) -> EntryT:
    if len(entries) != 1:
        raise ValueError(f"une seule entrée attendue, {len(entries)} trouvées")
    return entries[0]
