"""La laine de référence, son étiquette et ses échantillons (CLA-121, ADR 0030)."""

import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.domain.yarn import Yarn, YarnFamily, YarnLabel, YarnSwatch

SOURCE = {
    "kind": "reference_measurement",
    "reference": "https://www.garnstudio.com/yarn.php?show=drops-kid-silk&cid=8",
    "read_on": datetime.date(2026, 11, 12),
}
COMPOSITION = {
    "parts": [
        {"fiber": "mohair", "label_term": "Mohair", "percent": 75},
        {"fiber": "silk", "label_term": "Soie", "percent": 25},
    ]
}
LABEL: dict[str, object] = {
    "gauge": {
        "stitches": "23",
        "width": {"value": "10", "unit": "cm"},
        "rows": "30",
        "height": {"value": "10", "unit": "cm"},
    },
    "needles": [{"system": "mm", "original": "3,5 mm"}],
    "length_m": 210,
    "weight_g": 25,
    "care": "Lavage à la main, 30 °C max",
}
MEASURE = {"stitches": "22", "width": {"value": "10", "unit": "cm"}}
SWATCH: dict[str, object] = {
    "before": MEASURE,
    "needle": {"system": "mm", "original": "3,5 mm"},
    "stitch": "jersey",
    "knitted_on": datetime.date(2026, 11, 13),
    "source": {
        "kind": "user_swatch",
        "reference": "échantillon d’Isabelle",
        "read_on": datetime.date(2026, 11, 13),
    },
}
YARN: dict[str, object] = {
    "id": "drops-kid-silk",
    "brand": "DROPS",
    "name": "Kid-Silk",
    "composition": COMPOSITION,
    "superwash": None,
    "label": LABEL,
    "source": SOURCE,
}


def test_a_yarn_is_accepted_without_swatches() -> None:
    assert Yarn.model_validate(YARN).swatches == ()


def test_swatches_may_be_empty() -> None:
    assert Yarn.model_validate({**YARN, "swatches": []}).swatches == ()


def test_a_yarn_keeps_a_swatch_with_a_source() -> None:
    yarn = Yarn.model_validate({**YARN, "swatches": [SWATCH]})

    assert yarn.swatches[0].stitch == "jersey"
    assert yarn.swatches[0].after is None


def test_a_swatch_without_source_is_refused() -> None:
    without = {key: value for key, value in SWATCH.items() if key != "source"}
    with pytest.raises(ValidationError, match="source"):
        YarnSwatch.model_validate(without)


def test_a_swatch_needs_a_measure_before_or_after() -> None:
    without = {key: value for key, value in SWATCH.items() if key != "before"}
    with pytest.raises(ValidationError, match="avant ou après"):
        YarnSwatch.model_validate(without)


def test_a_swatch_after_blocking_alone_is_accepted() -> None:
    after_only = {**{k: v for k, v in SWATCH.items() if k != "before"}, "after": MEASURE}
    assert YarnSwatch.model_validate(after_only).before is None


def test_a_swatch_needs_its_needle() -> None:
    without = {key: value for key, value in SWATCH.items() if key != "needle"}
    with pytest.raises(ValidationError, match="needle"):
        YarnSwatch.model_validate(without)


def test_an_unknown_key_is_refused() -> None:
    with pytest.raises(ValidationError, match="blocking_change"):
        Yarn.model_validate({**YARN, "blocking_change": "1"})


def test_a_label_without_gauge_or_needles_is_accepted() -> None:
    label = YarnLabel.model_validate({"length_m": 235, "weight_g": 50})
    assert label.gauge is None
    assert label.needles is None


def test_a_label_range_gauge_keeps_its_bounds() -> None:
    gauge = {**LABEL, "gauge": {"stitches": {"low": "28", "high": "32"}, "width": MEASURE["width"]}}
    label = YarnLabel.model_validate(gauge)
    assert label.gauge is not None
    assert label.gauge.stitches != Decimal(28)


@pytest.mark.parametrize("count", [0, 3])
def test_a_label_has_one_or_two_needle_sizes(count: int) -> None:
    sizes = [{"system": "mm", "original": "3 mm"}] * count
    with pytest.raises(ValidationError):
        YarnLabel.model_validate({"needles": sizes})


def test_a_label_refuses_a_float_length() -> None:
    with pytest.raises(ValidationError):
        YarnLabel.model_validate({"length_m": 210.5})


def test_the_superwash_is_stated_even_when_unknown() -> None:
    without = {key: value for key, value in YARN.items() if key != "superwash"}
    with pytest.raises(ValidationError, match="superwash"):
        Yarn.model_validate(without)


def test_a_swatch_source_must_be_a_user_swatch() -> None:
    source = {**SOURCE, "kind": "model_inference"}
    with pytest.raises(ValidationError, match="user_swatch"):
        YarnSwatch.model_validate({**SWATCH, "source": source})


def test_a_swatch_stitch_cannot_be_empty() -> None:
    with pytest.raises(ValidationError, match="stitch"):
        YarnSwatch.model_validate({**SWATCH, "stitch": ""})


@pytest.mark.parametrize("field", ["brand", "name"])
def test_a_yarn_brand_and_name_cannot_be_empty(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        Yarn.model_validate({**YARN, field: ""})


def test_a_swatch_date_cannot_be_a_datetime() -> None:
    moment = datetime.datetime(2026, 11, 13, 10, 0, tzinfo=datetime.UTC)
    with pytest.raises(ValidationError, match="knitted_on"):
        YarnSwatch.model_validate({**SWATCH, "knitted_on": moment})


def test_the_yarn_weight_is_kept_as_the_maker_writes_it() -> None:
    text = "A (23 - 26 mailles) / 2 ply / lace"
    assert YarnLabel.model_validate({"yarn_weight": text}).yarn_weight == text


def test_the_yarn_weight_is_optional() -> None:
    assert YarnLabel.model_validate({}).yarn_weight is None


def test_a_blank_yarn_weight_is_refused() -> None:
    with pytest.raises(ValidationError, match="yarn_weight"):
        YarnLabel.model_validate({"yarn_weight": ""})


def composition(*parts: tuple[str, int]) -> dict[str, object]:
    return {
        "parts": [
            {"fiber": fiber, "label_term": fiber, "percent": percent} for fiber, percent in parts
        ]
    }


def family_of(parts: dict[str, object], superwash: bool | None) -> YarnFamily | None:
    return Yarn.model_validate({**YARN, "composition": parts, "superwash": superwash}).family


def test_a_superwash_merino_is_a_merino_family_with_superwash() -> None:
    assert family_of(composition(("merino", 100)), True) == YarnFamily(
        fiber="merino", superwash=True
    )


def test_the_family_is_the_majority_fiber() -> None:
    parts = composition(("alpaca", 65), ("polyamide", 28), ("merino", 7))

    assert family_of(parts, False) == YarnFamily(fiber="alpaca", superwash=False)


def test_a_yarn_with_no_published_superwash_has_no_family() -> None:
    assert family_of(composition(("merino", 100)), None) is None


def test_two_fibers_at_50_percent_have_no_family() -> None:
    assert family_of(composition(("merino", 50), ("nylon", 50)), True) is None
