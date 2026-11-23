"""Le modèle des cas d’évaluation et son hachage (CLA-126, ADR 0032)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.app.eval_cases import EvalCase, InjectedError, case_hash

SEVEN_TYPES = {
    "size_confusion",
    "unblocked_gauge",
    "unit_mismatch",
    "repeat_not_fitting",
    "count_mismatch",
    "missing_field",
    "prompt_injection",
}


REQUEST: dict[str, object] = {
    "head_circumference": {"value": "48", "unit": "cm", "provenance": "measured"},
    "ease": {"value": "-10", "unit": "percent", "provenance": "entered"},
    "swatch": {
        "needle": {"size": "4 mm", "kind": "straight"},
        "after_blocking": {"stitches": "20", "width": {"value": "10", "unit": "cm"}},
    },
    "needles": [{"size": "4 mm", "kind": "double_pointed"}],
    "stitch_multiple": {"repeat_multiple": 4, "repeat_offset": 0, "provenance": "entered"},
}


def _raw(**changes: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "id": "cas-1",
        "input": "Bonnet pour 3 ans.",
        "request": REQUEST,
        "expected": {"target_circumference_cm": "44.5", "cast_on_stitches": 88},
        "expected_reading": {},
    }
    raw.update(changes)
    return raw


def test_a_valid_case_loads() -> None:
    case = EvalCase.model_validate(_raw())
    assert case.expected.target_circumference_cm == Decimal("44.5")
    assert case.injected_error is None
    assert case.absent_fields == ()


def test_a_case_without_a_request_is_refused() -> None:
    raw = _raw()
    del raw["request"]
    with pytest.raises(ValidationError):
        EvalCase.model_validate(raw)


def test_a_case_without_an_expected_reading_is_refused() -> None:
    raw = _raw()
    del raw["expected_reading"]
    with pytest.raises(ValidationError):
        EvalCase.model_validate(raw)


def test_a_case_without_the_expected_cast_on_is_refused() -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_raw(expected={"target_circumference_cm": "44.5"}))


def test_an_expected_abstention_has_no_cast_on() -> None:
    case = EvalCase.model_validate(
        _raw(expected={"target_circumference_cm": "44.5", "abstain": True})
    )

    assert case.expected.abstain is True
    assert case.expected.cast_on_stitches is None


@pytest.mark.parametrize(
    "expected",
    [
        {"target_circumference_cm": "44.5", "cast_on_stitches": 88, "abstain": True},
        {"target_circumference_cm": "44.5", "abstain": False},
        {"target_circumference_cm": "44.5", "cast_on_stitches": None},
    ],
)
def test_an_expected_with_both_or_neither_is_refused(expected: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_raw(expected=expected))


def test_extra_fields_are_refused() -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_raw(surplus=1))


@pytest.mark.parametrize("bad", ["Cas 1", "cas_1", "CAS", ""])
def test_an_id_must_be_lowercase_slug(bad: str) -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_raw(id=bad))


def test_injected_error_accepts_the_seven_types() -> None:
    assert {member.value for member in InjectedError} == SEVEN_TYPES
    for value in SEVEN_TYPES:
        assert EvalCase.model_validate(_raw(injected_error=value)).injected_error == value


def test_injected_error_refuses_an_unknown_type() -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_raw(injected_error="inconnu"))


def test_absent_fields_refuse_duplicates() -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_raw(absent_fields=["brand", "brand"]))


def test_hash_is_stable_when_keys_are_reordered() -> None:
    first = EvalCase.model_validate(_raw())
    reordered = EvalCase.model_validate(
        {
            "expected": {"cast_on_stitches": 88, "target_circumference_cm": "44.5"},
            "expected_reading": {},
            "request": REQUEST,
            "input": "Bonnet pour 3 ans.",
            "id": "cas-1",
        }
    )
    assert case_hash(first) == case_hash(reordered)


def test_hash_changes_with_the_expected_value() -> None:
    other = _raw(expected={"target_circumference_cm": "45", "cast_on_stitches": 88})
    assert case_hash(EvalCase.model_validate(_raw())) != case_hash(EvalCase.model_validate(other))


def test_hash_changes_with_the_expected_reading() -> None:
    other = _raw(expected_reading={"edge": "garter"})
    assert case_hash(EvalCase.model_validate(_raw())) != case_hash(EvalCase.model_validate(other))


def test_hash_is_64_lowercase_hexadecimal_characters() -> None:
    digest = case_hash(EvalCase.model_validate(_raw()))
    assert len(digest) == 64
    assert digest == digest.lower()
    assert set(digest) <= set("0123456789abcdef")


def test_the_json_dump_renders_the_decimal_as_a_string() -> None:
    # Constaté par essai ; la doc de Pydantic ne le garantit pas.
    dumped = EvalCase.model_validate(_raw()).model_dump(mode="json")
    assert dumped["expected"] == {"target_circumference_cm": "44.5", "cast_on_stitches": 88}
