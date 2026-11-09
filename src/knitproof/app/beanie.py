"""Plan de bonnet : hauteur résolue, questions en attente (CLA-68, ADR 0020 et 0028).

Les mesures résolues (tour fini, jauges, multiple du point) arrivent explicites : leur
résolution depuis l’âge, la taille et l’aisance revient à CLA-66.
"""

from knitproof.domain.beanie import BeanieReview, BeanieSpecification
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.construction import CrownRule, MagicLoopAdvice
from knitproof.domain.measure import Length, SwatchMeasurement
from knitproof.domain.needle import KnittingMethod
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.question import PendingQuestion
from knitproof.domain.reference import ReferenceMeasurement
from knitproof.engine.beanie import beanie_plan
from knitproof.engine.cast_on import cast_on, flat_cast_on
from knitproof.library.loader import Library, load_library
from knitproof.library.lookup import rows_for_age


def plan_beanie(
    spec: BeanieSpecification,
    *,
    circumference: Length,
    stitch_multiple: StitchMultiple,
    after_blocking: SwatchMeasurement,
    before_blocking: SwatchMeasurement | None = None,
    library: Library | None = None,
) -> BeanieReview:
    """Le plan du bonnet, ou les questions qui manquent pour le calculer.

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
    if after_blocking.rows is None:
        questions.append(
            _question(
                NoticeCode.ROW_GAUGE_MISSING,
                "Combien de rangs sur quelle hauteur dans l’échantillon, après blocage ?",
            )
        )
    if height is None or spec.brim_height is None or after_blocking.rows is None:
        return BeanieReview(plan=None, notices=tuple(notices), questions=tuple(questions))
    stitches = _stitches(spec, circumference, stitch_multiple, after_blocking)
    review = beanie_plan(
        stitches=stitches,
        worked=spec.worked,
        stitch_multiple=stitch_multiple,
        finished_height=height,
        brim_height=spec.brim_height,
        folded_brim=spec.folded_brim,
        after_blocking=after_blocking,
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
