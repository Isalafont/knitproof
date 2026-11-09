"""L’exemple 3 ans donne le plan de l’exemple calculé à la main (CLA-68, CLA-69)."""

from pathlib import Path

import yaml

from knitproof.app.beanie import plan_beanie
from knitproof.app.beanie_request import BeanieRequest
from knitproof.engine.verification import verify

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "bonnet-3-ans.yaml"


def test_the_example_gives_88_stitches_and_the_hand_computed_rows() -> None:
    request = BeanieRequest.model_validate(yaml.safe_load(EXAMPLE.read_text(encoding="utf-8")))

    review = plan_beanie(
        request.specification,
        circumference=request.circumference,
        stitch_multiple=request.multiple,
        after_blocking=request.swatch.after_blocking,
        before_blocking=request.swatch.before_blocking,
    )

    assert review.plan is not None
    assert (review.plan.cast_on, review.plan.rows.total.rows) == (88, 75)
    assert (review.plan.rows.brim.rows, review.plan.body.rows) == (30, 28)
    assert review.plan.crown.round_count == 17
    assert verify(review.plan.pattern) == []
