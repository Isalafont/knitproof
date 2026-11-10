"""Rapport en texte : met en colonnes les entrées du rapport, ne calcule rien."""

from decimal import ROUND_HALF_EVEN, Decimal
from typing import assert_never

from knitproof.app.beanie import BeanieCalc
from knitproof.domain.beanie import BeaniePlan
from knitproof.domain.cast_on import CastOnResult
from knitproof.domain.ease import EaseUnit
from knitproof.domain.measure import Length, SwatchMeasurement
from knitproof.domain.report import Report, ReportEntry, ReportStatus

_TIMES = "\N{MULTIPLICATION SIGN}"
_MINUS = "\N{MINUS SIGN}"
_ENTERED = {"measured": "mesurée", "entered": "saisie"}

_OK_LABEL = "OK"
_COLUMN = 12
_INDENT = " " * _COLUMN


def render(report: Report) -> str:
    """Un bloc par entrée, séparés par une ligne vide ; une ligne « OK » sans entrée."""
    if not report.entries:
        return f"{_OK_LABEL:<{_COLUMN}}Aucun écart sur les comptes vérifiés."
    return "\n\n".join(_describe(entry) for entry in report.entries)


def _describe(entry: ReportEntry) -> str:
    first, *rest = entry.lines
    title = first if entry.round is None else f"Rang {entry.round} — {first}"
    lines = [*rest, f"Décidé par : {entry.decided_by.label}"]
    head = f"{_status_label(entry.status):<{_COLUMN}}{title}"
    return "\n".join([head, *(f"{_INDENT}{line}" for line in lines)])


def _status_label(status: ReportStatus) -> str:
    match status:
        case ReportStatus.ERROR:
            return "ERREUR"
        case ReportStatus.WARNING:
            return "ALERTE"
        case ReportStatus.NEEDS_REVIEW:
            return "À VÉRIFIER"
        case ReportStatus.REJECTED:
            return "REJETÉ"
        case _:
            assert_never(status)


def render_calc(calc: BeanieCalc) -> str:
    """Le résumé du plan, puis les entrées du rapport, puis les questions en attente."""
    report = calc.report
    blocks = []
    if report.result is not None and calc.cast_on is not None and calc.gauge.gauge is not None:
        blocks.append(_summary(calc, report.result, calc.cast_on, calc.gauge.gauge))
    blocks.extend(_describe(entry) for entry in report.entries)
    blocks.extend(_ask(question.text) for question in report.questions)
    return "\n\n".join(blocks)


def _ask(text: str) -> str:
    return f"{'QUESTION':<{_COLUMN}}{text}"


def _summary(
    calc: BeanieCalc, plan: BeaniePlan, cast: CastOnResult, swatch: SwatchMeasurement
) -> str:
    request = calc.request
    ease = request.ease
    head = request.head_circumference
    rows = swatch.rows_per_10_cm
    ease_text = _signed(ease.value) + (" %" if ease.unit is EaseUnit.PERCENT else f" {ease.unit}")
    if ease.unit is EaseUnit.PERCENT:
        factor = f"{_number(head.value)} {_TIMES} {_number((100 + ease.value).scaleb(-2))}"
    else:
        factor = (
            f"{_number(head.value)} {'+' if ease.value >= 0 else _MINUS} {_number(abs(ease.value))}"
        )
    mult = request.multiple.repeat_multiple
    cast_line = (
        f"{_number(cast.raw_stitches)} m calculées "
        f"({_number(calc.circumference.value)} {_TIMES} {_number(swatch.stitches_per_10_cm)} / 10)"
        f" \N{RIGHTWARDS ARROW} {cast.stitches} m, multiple de {mult}"
    )
    lines = [
        (
            "Échantillon",
            f"{_number(swatch.stitches_per_10_cm)} m / 10 cm, après blocage"
            " (source : votre échantillon)",
        ),
        ("Aisance", f"{ease_text} : {_ENTERED[request.ease.provenance.value]}"),
        ("Tour visé", f"{_length(calc.circumference)} ({factor})"),
        ("Montage", cast_line),
        ("", f"Tour fini réel : {_number(cast.finished_cm)} cm"),
    ]
    if plan.cast_on != cast.stitches:
        lines.append(("", f"Montage à plat : {plan.cast_on} m, lisières comprises"))
    lines.append(("Hauteur", _height(calc, plan, rows)))
    lines.append(("Bord", _brim(calc, plan)))
    crown = plan.crown
    lines.append(
        (
            "Calotte",
            f"{crown.round_count} rangs, {crown.decrease_rounds} rangs de diminution, "
            f"{crown.remaining} m restantes, environ {_number(plan.depth_cm, 1)} cm",
        )
    )
    lines.append(
        (
            "Corps",
            f"{plan.body.rows} rangs ({plan.rows.total.rows} {_MINUS} {plan.rows.brim.rows} "
            f"{_MINUS} {crown.round_count})",
        )
    )
    needle_lines = [line for info in calc.needles for line in info.text.splitlines()]
    lines.extend(("Aiguilles" if i == 0 else "", line) for i, line in enumerate(needle_lines))
    return "\n".join(f"{label:<{_COLUMN}}{text}" for label, text in lines)


def _height(calc: BeanieCalc, plan: BeaniePlan, rows: Decimal | None) -> str:
    request = calc.request
    finished = _length(plan.finished_height)
    gauge = "" if rows is None else f" ({_number(rows)} rangs / 10 cm{_rows_source(calc)})"
    count = plan.rows.total.rows
    if request.folded_brim and request.brim_height is not None:
        knitted = plan.finished_height.in_cm + request.brim_height.in_cm
        return (
            f"{finished} finis + {_length(request.brim_height)} de revers "
            f"= {_number(knitted)} cm tricotés : {count} rangs{gauge}"
        )
    return f"{finished} finis : {count} rangs{gauge}"


def _rows_source(calc: BeanieCalc) -> str:
    swatch = calc.request.swatch
    source = (
        None
        if swatch is None or swatch.after_blocking is None
        else swatch.after_blocking.rows_source
    )
    if source is None:
        return ""
    check = ", À VÉRIFIER" if source.to_verify else ""
    return f"{check}, d’après {source.reference}"


def _brim(calc: BeanieCalc, plan: BeaniePlan) -> str:
    height = calc.request.brim_height
    count = plan.rows.brim.rows
    if calc.request.folded_brim and height is not None:
        return f"{count} rangs (le revers se tricote deux fois : 2 {_TIMES} {_length(height)})"
    return f"{count} rangs"


def _length(length: Length) -> str:
    return f"{_number(length.value)} {length.unit.value}"


def _signed(value: Decimal) -> str:
    return f"{_MINUS}{_number(abs(value))}" if value < 0 else _number(value)


def _number(value: Decimal, places: int = 2) -> str:
    """Décimal à la virgule, sans zéros inutiles ; présentation seulement (`ROUND_HALF_EVEN`)."""
    shown = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    return format(shown.normalize(), "f").replace(".", ",")
