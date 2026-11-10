"""Rang d’ajustement du bord au corps, réparti puis vérifié (CLA-103, ADR 0025)."""

from itertools import groupby

from knitproof.domain.pattern import Op, Pattern, Repeat, RepeatBlock, Round, Stitch, Work
from knitproof.domain.transition import Transition, TransitionRefusal, TransitionRejection
from knitproof.engine.verification import verify


def build_transition(edge_stitches: int, body_stitches: int) -> Transition | TransitionRefusal:
    """Le rang qui passe du bord au corps, changements répartis (ADR 0019, décision 2)."""
    if edge_stitches == body_stitches:
        return Transition(
            edge_stitches=edge_stitches, body_stitches=body_stitches, adjustment_round=None
        )
    refusal = _refusal(edge_stitches, body_stitches)
    if refusal is not None:
        return refusal
    change = Stitch.K2TOG if body_stitches < edge_stitches else Stitch.M1
    changes = abs(body_stitches - edge_stitches)
    worked = edge_stitches - change.consumes * changes
    round_ = Round(
        start=1, ops=_compact(_sections(worked, changes), change), stated_count=body_stitches
    )
    transition = Transition(
        edge_stitches=edge_stitches, body_stitches=body_stitches, adjustment_round=round_
    )
    findings = verify(Pattern(cast_on=edge_stitches, rounds=(round_,)))
    if findings:
        raise RuntimeError(f"rang d’ajustement non vérifié : {findings}")
    return transition


def _refusal(edge: int, body: int) -> TransitionRefusal | None:
    fewest = edge - edge // Stitch.K2TOG.consumes  # k2tog partout
    most = edge + edge  # un m1 après chaque maille
    if body < fewest:
        reason, limit = TransitionRejection.TOO_MANY_DECREASES, fewest
    elif body > most:
        reason, limit = TransitionRejection.TOO_MANY_INCREASES, most
    else:
        return None
    return TransitionRefusal(edge_stitches=edge, body_stitches=body, reason=reason, limit=limit)


def _sections(worked: int, changes: int) -> list[int]:
    return [(i + 1) * worked // changes - i * worked // changes for i in range(changes)]


def _compact(sizes: list[int], change: Stitch) -> tuple[Op, ...]:
    ops: list[Op] = []
    for size, group in groupby(sizes):
        section: tuple[Op, ...] = (Work(work=size), change) if size > 0 else (change,)
        times = len(list(group))
        if times > 1:
            ops.append(Repeat(repeat=RepeatBlock(body=section, times=times)))
        else:
            ops.extend(section)
    return tuple(ops)
