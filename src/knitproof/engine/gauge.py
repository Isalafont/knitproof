"""Résolution de la jauge du calcul selon l’ordre de confiance (CLA-66, ADR 0008).

Pur : ni fichier, ni réseau, ni modèle ; aucune valeur n’est inventée, une jauge qui manque
devient une question en attente.
"""

from knitproof.domain.gauge import GaugeRange, GaugeSource, LabelGauge, ResolvedGauge
from knitproof.domain.measure import SwatchMeasurement
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.question import PendingQuestion

_BLOCK = "bloquer (laver puis sécher)"


def resolve_gauge(
    *,
    blocked: SwatchMeasurement | None = None,
    unblocked: SwatchMeasurement | None = None,
    unknown: SwatchMeasurement | None = None,
    label: LabelGauge | None = None,
) -> ResolvedGauge:
    """Après blocage, non bloqué, état inconnu (question), étiquette, rien (question)."""
    if blocked is not None:
        return ResolvedGauge(gauge=blocked, source=GaugeSource.BLOCKED)
    if unblocked is not None:
        return ResolvedGauge(
            gauge=unblocked,
            source=GaugeSource.UNBLOCKED,
            notices=(_unblocked_notice(),),
        )
    if unknown is not None:
        return ResolvedGauge(gauge=None, source=None, questions=(_blocking_question(),))
    if label is not None:
        return _from_label(label)
    return ResolvedGauge(
        gauge=None,
        source=None,
        questions=(
            _question(
                NoticeCode.GAUGE_MISSING,
                "Quelle est ta jauge ? Mesure un échantillon bloqué (lavé puis séché) : "
                "mailles sur une largeur, rangs sur une hauteur.",
            ),
        ),
    )


def _from_label(label: LabelGauge) -> ResolvedGauge:
    stitches, rows = label.stitches, label.rows
    ranged = [
        name
        for name, value in (("mailles", stitches), ("rangs", rows))
        if isinstance(value, GaugeRange)
    ]
    if isinstance(stitches, GaugeRange) or isinstance(rows, GaugeRange):
        return ResolvedGauge(
            gauge=None,
            source=None,
            questions=(
                _question(
                    NoticeCode.LABEL_GAUGE_RANGE,
                    f"L’étiquette donne une fourchette de {' et de '.join(ranged)} : "
                    "quelle valeur de la fourchette retenir ?",
                ),
            ),
        )
    gauge = SwatchMeasurement(stitches=stitches, width=label.width, rows=rows, height=label.height)
    text = (
        "À VÉRIFIER : jauge du fabricant, état de blocage inconnu\n"
        "Fais un échantillon, bloque-le (lave-le puis sèche-le), puis mesure-le pour remplacer "
        "la jauge de l’étiquette."
    )
    notice = Notice(status=NoticeStatus.WARNING, code=NoticeCode.GAUGE_FROM_LABEL, text=text)
    return ResolvedGauge(gauge=gauge, source=GaugeSource.LABEL, notices=(notice,))


def _unblocked_notice() -> Notice:
    text = (
        "À VÉRIFIER : le calcul suit l’échantillon non bloqué\n"
        f"Pense à {_BLOCK} l’échantillon avant de le mesurer : la laine change en lavage."
    )
    return Notice(status=NoticeStatus.WARNING, code=NoticeCode.GAUGE_UNBLOCKED, text=text)


def _blocking_question() -> PendingQuestion:
    text = (
        "L’as-tu bloqué (lavé puis séché) ? Réponds dans le fichier : renomme `unknown_blocking` "
        "en `after_blocking` si oui (mesures après blocage), ou en `before_blocking` si non."
    )
    return PendingQuestion(
        code=NoticeCode.GAUGE_BLOCKING_UNKNOWN, text=text, options=("oui", "non")
    )


def _question(code: NoticeCode, text: str) -> PendingQuestion:
    return PendingQuestion(code=code, text=text, options=())
