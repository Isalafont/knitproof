"""Le modèle des cas d’évaluation et son hachage (CLA-126, ADR 0032)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from knitproof.evals.case import EvalCase, InjectedError, case_hash

SEVEN_TYPES = {
    "size_confusion",
    "unblocked_gauge",
    "unit_mismatch",
    "repeat_not_fitting",
    "count_mismatch",
    "missing_field",
    "prompt_injection",
}


def _raw(**changes: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "id": "cas-1",
        "input": "Bonnet pour 3 ans.",
        "expected": {"target_circumference_cm": "44.5"},
    }
    raw.update(changes)
    return raw


def test_a_valid_case_loads() -> None:
    case = EvalCase.model_validate(_raw())
    assert case.expected.target_circumference_cm == Decimal("44.5")
    assert case.injected_error is None
    assert case.absent_fields == ()


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
            "expected": {"target_circumference_cm": "44.5"},
            "input": "Bonnet pour 3 ans.",
            "id": "cas-1",
        }
    )
    assert case_hash(first) == case_hash(reordered)


def test_hash_changes_with_the_expected_value() -> None:
    other = _raw(expected={"target_circumference_cm": "45"})
    assert case_hash(EvalCase.model_validate(_raw())) != case_hash(EvalCase.model_validate(other))


def test_hash_is_64_lowercase_hexadecimal_characters() -> None:
    digest = case_hash(EvalCase.model_validate(_raw()))
    assert len(digest) == 64
    assert digest == digest.lower()
    assert set(digest) <= set("0123456789abcdef")


def test_the_json_dump_renders_the_decimal_as_a_string() -> None:
    # Constaté par essai ; la doc de Pydantic ne le garantit pas.
    dumped = EvalCase.model_validate(_raw()).model_dump(mode="json")
    assert dumped["expected"] == {"target_circumference_cm": "44.5"}
