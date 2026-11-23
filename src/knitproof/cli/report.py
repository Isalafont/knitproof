"""Rapport en texte : met en colonnes les entrées du rapport, ne calcule rien."""

from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import assert_never

from knitproof.app.baseline import BaselineResult, ProviderResult
from knitproof.app.beanie import BeanieCalc
from knitproof.app.beanie_request import BeanieRequest
from knitproof.app.decisions import ANSWERABLE_QUESTIONS
from knitproof.domain.beanie import BeaniePlan, RowRounding
from knitproof.domain.cast_on import CastOnResult
from knitproof.domain.decision import Decision
from knitproof.domain.ease import EaseUnit
from knitproof.domain.gauge import GaugeSource
from knitproof.domain.measure import Length, LengthUnit, SwatchMeasurement
from knitproof.domain.question import PendingQuestion
from knitproof.domain.report import DecidedBy, Report, ReportEntry, ReportStatus

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
    """Le résumé du plan, les entrées du rapport, les choix, puis les questions en attente."""
    report = calc.report
    blocks = []
    if report.result is not None and calc.cast_on is not None and calc.gauge.gauge is not None:
        blocks.append(_summary(calc, report.result, calc.cast_on, calc.gauge.gauge))
    blocks.extend(_describe(entry) for entry in report.entries)
    blocks.extend(_decided(decision) for decision in report.decisions)
    blocks.extend(_ask(question) for question in report.questions)
    return "\n\n".join(blocks)


def _decided(decision: Decision) -> str:
    """Le choix de la personne : question, option, date, motif, puis qui a décidé."""
    lines = [f"Le {decision.decided_on:%d/%m/%Y}"]
    if decision.reason is not None:
        lines.append(f"Motif : {decision.reason}")
    lines.append(f"Décidé par : {DecidedBy.PERSON.label}")
    head = f"{'CHOIX':<{_COLUMN}}{decision.question} : {decision.choice}"
    return "\n".join([head, *(f"{_INDENT}{line}" for line in lines)])


def _ask(question: PendingQuestion) -> str:
    """La question ; son code et ses choix seulement si une décision peut y répondre."""
    lines = [f"{'QUESTION':<{_COLUMN}}{question.text}"]
    if question.code in ANSWERABLE_QUESTIONS:
        lines.append(f"{_INDENT}Code : {question.code}")
        lines.append(f"{_INDENT}Choix : {', '.join(question.options)}")
    return "\n".join(lines)


def _summary(
    calc: BeanieCalc, plan: BeaniePlan, cast: CastOnResult, swatch: SwatchMeasurement
) -> str:
    request = calc.request
    ease = request.ease
    head_cm = request.head_circumference.in_cm
    rows = swatch.rows_per_10_cm
    ease_text = _signed(ease.value) + (" %" if ease.unit is EaseUnit.PERCENT else f" {ease.unit}")
    if ease.unit is EaseUnit.PERCENT:
        factor = f"{_number(head_cm)} {_TIMES} {_number((100 + ease.value).scaleb(-2))}"
    else:
        factor = (
            f"{_number(head_cm)} {'+' if ease.value >= 0 else _MINUS} {_number(abs(ease.value))}"
        )
    conversions = _conversions(request)
    multiple = request.multiple
    mult = f"{multiple.repeat_multiple}" + (
        f" + {multiple.repeat_offset}" if multiple.repeat_offset else ""
    )
    cast_line = (
        f"{_number(cast.raw_stitches)} m calculées "
        f"({_number(calc.circumference.in_cm)} {_TIMES} {_number(swatch.stitches_per_10_cm)} / 10)"
        f" \N{RIGHTWARDS ARROW} {cast.stitches} m, multiple de {mult}"
    )
    lines: list[tuple[str, str]] = [
        ("Échantillon", f"{_number(swatch.stitches_per_10_cm)} m / 10 cm, {_gauge_source(calc)}"),
        ("Aisance", f"{ease_text} : {_ENTERED[request.ease.provenance.value]}"),
        *conversions,
        ("Tour visé", f"{_cm(calc.circumference)} ({factor})"),
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
    lines.append(("Corps", _body(plan)))
    needle_lines = [line for info in calc.needles for line in info.text.splitlines()]
    lines.extend(("Aiguilles" if i == 0 else "", line) for i, line in enumerate(needle_lines))
    return "\n".join(f"{label:<{_COLUMN}}{text}" for label, text in lines)


def _body(plan: BeaniePlan) -> str:
    """Les rangs du corps, avec la différence puis l’ajustement de parité à plat."""
    total, brim, crown = plan.rows.total.rows, plan.rows.brim.rows, plan.crown.round_count
    difference = total - brim - crown
    text = f"{plan.body.rows} rangs ({total} {_MINUS} {brim} {_MINUS} {crown}"
    if plan.body.rule is RowRounding.DIFFERENCE_FLAT_PARITY:
        gap = plan.body.rows - difference
        sign = "+" if gap > 0 else _MINUS
        text += f" = {difference}, {sign} {abs(gap)} : bord et corps en nombre pair à plat"
    return text + ")"


def _gauge_source(calc: BeanieCalc) -> str:
    origin = DecidedBy.PERSON.label if calc.gauge.decision else "votre échantillon"
    match calc.gauge.source:
        case GaugeSource.BLOCKED:
            return f"après blocage (source : {origin})"
        case GaugeSource.UNBLOCKED:
            return f"avant blocage, À VÉRIFIER (source : {origin})"
        case GaugeSource.LABEL:
            return "étiquette, À VÉRIFIER (source : fabricant)"
        case None:
            raise ValueError("une jauge résolue a une source")
        case _:
            assert_never(calc.gauge.source)


def _height(calc: BeanieCalc, plan: BeaniePlan, rows: Decimal | None) -> str:
    request = calc.request
    finished = _cm(plan.finished_height)
    gauge = "" if rows is None else f" ({_number(rows)} rangs / 10 cm{_rows_source(calc)})"
    count = plan.rows.total.rows
    if request.folded_brim and request.brim_height is not None:
        knitted = plan.finished_height.in_cm + request.brim_height.in_cm
        return (
            f"{finished} finis + {_cm(request.brim_height)} de revers "
            f"= {_number(knitted)} cm tricotés : {count} rangs{gauge}"
        )
    return f"{finished} finis : {count} rangs{gauge}"


def _rows_source(calc: BeanieCalc) -> str:
    """La source des rangs, relue dans la demande selon la source de la jauge retenue."""
    swatch = calc.request.swatch
    measure = None
    if swatch is not None:
        match calc.gauge.source:
            case _ if calc.gauge.decision is not None:
                measure = swatch.unknown_blocking
            case GaugeSource.BLOCKED:
                measure = swatch.after_blocking
            case GaugeSource.UNBLOCKED:
                measure = swatch.before_blocking
            case _:
                measure = None
    source = None if measure is None else measure.rows_source
    if source is None:
        return ""
    check = ", À VÉRIFIER" if source.to_verify else ""
    return f"{check}, d’après {source.reference}"


def _brim(calc: BeanieCalc, plan: BeaniePlan) -> str:
    height = calc.request.brim_height
    count = plan.rows.brim.rows
    if calc.request.folded_brim and height is not None:
        return f"{count} rangs (le revers se tricote deux fois : 2 {_TIMES} {_cm(height)})"
    return f"{count} rangs"


def _conversions(request: BeanieRequest) -> list[tuple[str, str]]:
    """Une ligne qui rappelle chaque saisie en pouces, convertie en cm ; rien sans pouces."""
    inputs = (
        (request.head_circumference, "tour de tête"),
        (request.total_height, "hauteur finie"),
        (request.brim_height, "bord"),
    )
    shown = [
        f"{_number(length.value)} in = {_cm(length)} ({name})"
        for length, name in inputs
        if length is not None and length.unit is LengthUnit.IN
    ]
    return [("Conversions", " ; ".join(shown))] if shown else []


def _cm(length: Length) -> str:
    return f"{_number(length.in_cm)} cm"


def _signed(value: Decimal) -> str:
    return f"{_MINUS}{_number(abs(value))}" if value < 0 else _number(value)


def _number(value: Decimal, places: int = 2) -> str:
    """Décimal à la virgule, sans zéros inutiles ; présentation seulement (`ROUND_HALF_EVEN`)."""
    shown = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    return format(shown.normalize(), "f").replace(".", ",")


def render_baseline(result: BaselineResult, written: Path) -> str:
    """Une ligne par entrée : « LLM seul » et, s’il est mesuré, « knitproof » avec la lecture."""
    labels = [_entry_label(item) for item in result.providers]
    width = max(map(len, labels), default=0) + 2
    lines = [
        f"{label:<{width}}{_entry_columns(item)}"
        for label, item in zip(labels, result.providers, strict=True)
    ]
    lines.append(f"Résultat : {written}")
    return "\n".join(lines)


def _entry_columns(item: ProviderResult) -> str:
    column = item.knitproof
    if column is None:
        return (
            f"{item.correct}/{item.total}  "
            f"[{_comma(item.low)} ; {_comma(item.high)}]  abstentions : {item.abstentions}"
        )
    return (
        f"LLM seul {item.correct}/{item.total}  [{_comma(item.low)} ; {_comma(item.high)}]  "
        f"knitproof {column.correct}/{column.total}  "
        f"[{_comma(column.low)} ; {_comma(column.high)}]  "
        f"lecture {column.fields_exact}/{column.fields_expected}  inventés {column.invented}  "
        f"abstentions : {item.abstentions} ; knitproof {column.abstentions}"
    )


def _entry_label(item: ProviderResult) -> str:
    model = f":{item.model}" if item.model else ""
    host = f"@{item.host}" if item.host else ""
    return f"{item.provider}{model}{host}"


def _comma(value: Decimal) -> str:
    return str(value).replace(".", ",")
