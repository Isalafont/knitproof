"""Résolution de la jauge du calcul selon l’ordre de confiance (CLA-66, ADR 0008).

Pur : ni fichier, ni réseau, ni modèle ; aucune valeur n’est inventée, une jauge qui manque
devient une question en attente.
"""

from decimal import Decimal

from knitproof.domain.gauge import GaugeRange, GaugeSource, LabelGauge, ResolvedGauge
from knitproof.domain.measure import DIVISION, EXACT, Length, SwatchMeasurement
from knitproof.domain.notice import Notice, NoticeCode, NoticeStatus
from knitproof.domain.question import PendingQuestion

_BLOCK = "bloquer (laver puis sécher)"

# Décision d’Isabelle, question 14 (27/10/2026) : un écart d’au moins 5 % avec l’étiquette est
# signalé ; modifiable.
LABEL_GAUGE_THRESHOLD_PERCENT = 5
_HUNDRED = Decimal(100)

_ROWS_TEXT = (
    "ta jauge en rangs diffère de l’étiquette ; la hauteur est calculée sur ton échantillon"
)


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


def gauge_differs_from_label(swatch: SwatchMeasurement, label: LabelGauge) -> tuple[Notice, ...]:
    """Un `warning` par grandeur (mailles, rangs) à au moins 5 % de la borne la plus proche.

    Dans la fourchette, ou sous le seuil, aucun constat. Le texte donne le sens de correction
    des mailles, jamais une taille d’aiguilles ni une décision.
    """
    notices = []
    stitches = _gap(swatch.stitches, swatch.width, label.stitches, label.width)
    if stitches is not None:
        direction = (
            "trop de mailles pour 10 cm : aiguilles plus grosses"
            if stitches > 0
            else "pas assez de mailles pour 10 cm : aiguilles plus fines"
        )
        text = (
            f"Ton échantillon : {_per_10_cm(swatch.stitches, swatch.width)} m pour 10 cm ; "
            f"étiquette : {_label_text(label.stitches, label.width)} m pour 10 cm\n{direction}"
        )
        notices.append(_notice(text))
    if (
        swatch.rows is not None
        and swatch.height is not None
        and label.rows is not None
        and label.height is not None
        and _gap(swatch.rows, swatch.height, label.rows, label.height) is not None
    ):
        notices.append(_notice(_ROWS_TEXT))
    return tuple(notices)


def _gap(
    value: Decimal, length: Length, label: Decimal | GaugeRange, label_length: Length
) -> int | None:
    """Le sens (+1 trop, -1 pas assez) d’un écart d’au moins 5 % à la borne la plus proche.

    Produits croisés exacts : l’écart relatif `|S/Ws - L/Wl| / (L/Wl)` vaut au moins 5 % quand
    `100 * |S*Wl - L*Ws| >= 5 * L*Ws` ; aucun quotient, donc aucun arrondi au seuil.
    """
    bounds = (label.low, label.high) if isinstance(label, GaugeRange) else (label, label)
    scaled = EXACT.multiply(value, label_length.in_cm)
    for bound, sign in ((bounds[0], -1), (bounds[1], 1)):
        reference = EXACT.multiply(bound, length.in_cm)
        if (scaled - reference) * sign <= 0:
            continue
        gap = EXACT.multiply(_HUNDRED, abs(EXACT.subtract(scaled, reference)))
        if gap >= EXACT.multiply(LABEL_GAUGE_THRESHOLD_PERCENT, reference):
            return sign
    return None


def _notice(text: str) -> Notice:
    return Notice(status=NoticeStatus.WARNING, code=NoticeCode.GAUGE_DIFFERS_FROM_LABEL, text=text)


def _per_10_cm(value: Decimal, length: Length) -> str:
    """Pour l’affichage seulement : le quotient n’entre dans aucun contrôle."""
    return _shown(DIVISION.divide(EXACT.multiply(value, Decimal(10)), length.in_cm))


def _label_text(label: Decimal | GaugeRange, length: Length) -> str:
    if isinstance(label, GaugeRange):
        return f"{_per_10_cm(label.low, length)} à {_per_10_cm(label.high, length)}"
    return _per_10_cm(label, length)


def _shown(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")).normalize(), "f").replace(".", ",")
