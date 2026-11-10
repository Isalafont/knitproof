"""Provenance d’une valeur de bibliothèque : source, date de lecture, « À VÉRIFIER » (CLA-67)."""

import datetime

import pytest
from pydantic import ValidationError

from knitproof.domain.provenance import Provenance, SourcedEntry, SourceKind

READ_ON = datetime.date(2026, 11, 9)


def test_a_provenance_keeps_its_fields() -> None:
    provenance = Provenance(
        kind=SourceKind.REFERENCE_MEASUREMENT,
        reference="Auteur, titre, URL",
        read_on=READ_ON,
        location="tableau 2",
    )

    assert provenance.kind is SourceKind.REFERENCE_MEASUREMENT
    assert provenance.read_on == READ_ON
    assert provenance.location == "tableau 2"
    assert provenance.to_verify is False


@pytest.mark.parametrize("reference", ["", "   "])
def test_an_empty_reference_is_refused(reference: str) -> None:
    with pytest.raises(ValidationError, match="reference"):
        Provenance(kind=SourceKind.FIBER_LIBRARY, reference=reference, read_on=READ_ON)


def test_a_missing_reference_is_refused() -> None:
    with pytest.raises(ValidationError, match="reference"):
        Provenance.model_validate({"kind": "fiber_library", "read_on": READ_ON})


@pytest.mark.parametrize(
    "read_on",
    [
        datetime.datetime(2026, 11, 9, 10, 0),
        datetime.datetime(2026, 11, 9),
        "9 novembre",
        20261109,
        None,
    ],
)
def test_read_on_must_be_a_date(read_on: object) -> None:
    with pytest.raises(ValidationError, match="read_on"):
        Provenance.model_validate({"kind": "fiber_library", "reference": "x", "read_on": read_on})


def test_person_decision_is_a_source_kind() -> None:
    provenance = Provenance(
        kind=SourceKind.PERSON_DECISION, reference="Isabelle, ADR 0019", read_on=READ_ON
    )

    assert provenance.kind is SourceKind.PERSON_DECISION


def test_model_inference_exists_in_the_domain() -> None:
    assert SourceKind.MODEL_INFERENCE.value == "model_inference"
    assert len(SourceKind) == 10


def test_a_to_verify_status_marks_the_provenance() -> None:
    entry = SourcedEntry.model_validate(
        {
            "id": "a",
            "status": "to_verify",
            "source": {"kind": "fiber_library", "reference": "x", "read_on": READ_ON},
        }
    )

    assert entry.source.to_verify is True


def test_an_entry_without_status_is_not_to_verify() -> None:
    entry = SourcedEntry.model_validate(
        {"id": "a", "source": {"kind": "fiber_library", "reference": "x", "read_on": READ_ON}}
    )

    assert entry.source.to_verify is False


def test_to_verify_cannot_be_written_in_the_source() -> None:
    with pytest.raises(ValidationError, match="to_verify"):
        SourcedEntry.model_validate(
            {
                "id": "a",
                "source": {
                    "kind": "fiber_library",
                    "reference": "x",
                    "read_on": READ_ON,
                    "to_verify": True,
                },
            }
        )


def test_an_entry_without_source_is_refused() -> None:
    with pytest.raises(ValidationError, match="source"):
        SourcedEntry.model_validate({"id": "a"})


def test_an_unknown_status_is_refused() -> None:
    with pytest.raises(ValidationError, match="status"):
        SourcedEntry.model_validate(
            {
                "id": "a",
                "status": "verified",
                "source": {"kind": "fiber_library", "reference": "x", "read_on": READ_ON},
            }
        )
