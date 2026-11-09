"""L’exemple 3 ans donne le plan de l’exemple calculé à la main (CLA-68)."""

from decimal import Decimal
from pathlib import Path

import yaml

from knitproof.app.beanie import plan_beanie
from knitproof.domain.beanie import BeanieSpecification
from knitproof.domain.cast_on import StitchMultiple
from knitproof.domain.measure import EXACT, Length, SwatchMeasurement
from knitproof.domain.needle import Needle, NeedleKind, NeedleSize, NeedleSystem
from knitproof.engine.verification import verify

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "bonnet-3-ans.yaml"
HUNDRED = Decimal(100)


def _length(raw: dict[str, str]) -> Length:
    """La longueur d’une ligne du YAML, sans sa provenance."""
    return Length.model_validate({key: raw[key] for key in ("value", "unit")})


def test_the_example_gives_88_stitches_and_the_hand_computed_rows() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    head = _length(data["head_circumference"])
    ease = Decimal(data["ease"]["value"])
    circumference = Length(
        value=EXACT.multiply(head.value, HUNDRED + ease) / HUNDRED, unit=head.unit
    )
    spec = BeanieSpecification(
        total_height=_length(data["total_height"]),
        brim_height=_length(data["brim_height"]),
        folded_brim=data["folded_brim"],
        needles=(
            Needle(
                size=NeedleSize(system=NeedleSystem.MM, original="4"),
                kind=NeedleKind.DOUBLE_POINTED,
            ),
        ),
    )

    review = plan_beanie(
        spec,
        circumference=circumference,
        stitch_multiple=StitchMultiple(repeat_multiple=4, repeat_offset=0),
        after_blocking=SwatchMeasurement.model_validate(data["swatch"]["after_blocking"]),
        before_blocking=SwatchMeasurement.model_validate(data["swatch"]["before_blocking"]),
    )

    assert review.plan is not None
    assert (review.plan.cast_on, review.plan.rows.total.rows) == (88, 75)
    assert (review.plan.rows.brim.rows, review.plan.body.rows) == (30, 28)
    assert review.plan.crown.round_count == 17
    assert verify(review.plan.pattern) == []
