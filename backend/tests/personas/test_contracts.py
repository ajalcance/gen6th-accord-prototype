"""Pure H2 contract tests; deliberately do not require database fixtures."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.contracts import PersonaDraft, PersonaVersion


def draft(**changes: object) -> PersonaDraft:
    fields: dict[str, object] = {
        "name": "Fictional Nova",
        "biography": "A fictional editorial character.",
        "human_contribution": "Original character concept and illustration.",
        "ai_disclosure": "Fictional synthetic persona; no real person represented.",
    }
    fields.update(changes)
    return PersonaDraft.model_validate(fields)


@pytest.mark.parametrize("field", ["actor_id", "workspace_id", "approved", "recorded_at"])
def test_input_rejects_attribution_and_decisions(field: str) -> None:
    with pytest.raises(ValidationError):
        draft(**{field: "client-assertion"})


@pytest.mark.parametrize("field", ["name", "biography", "human_contribution", "ai_disclosure"])
def test_required_statements_are_not_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        draft(**{field: "   "})


def test_name_is_trimmed_and_bounded() -> None:
    assert draft(name="  Fictional Nova  ").name == "Fictional Nova"
    with pytest.raises(ValidationError):
        draft(name="n" * 81)


def test_statement_limit_and_no_sample_marker() -> None:
    with pytest.raises(ValidationError):
        draft(biography="b" * 501)
    with pytest.raises(ValidationError):
        draft(fixture="false")
    with pytest.raises(ValidationError):
        draft(fixture=False)


def version() -> PersonaVersion:
    return PersonaVersion(
        persona_id=uuid4(),
        workspace_id=uuid4(),
        version_id=uuid4(),
        revision=1,
        creator_ref="pseudonymous-creator",
        recorded_at=datetime.now(UTC),
        content=draft(),
    )


@pytest.mark.parametrize("field,value", [("revision", 2), ("name", "Changed")])
def test_version_and_nested_content_are_immutable(field: str, value: object) -> None:
    snapshot = version()
    target = snapshot if field == "revision" else snapshot.content
    with pytest.raises(ValidationError):
        setattr(target, field, value)


def test_version_rejects_ambiguous_receipt_time_and_revision() -> None:
    fields = version().model_dump()
    fields["recorded_at"] = datetime(2026, 10, 1)
    with pytest.raises(ValidationError):
        PersonaVersion.model_validate(fields)
    fields["recorded_at"] = datetime.now(UTC)
    for revision in (0, True, "1"):
        fields["revision"] = revision
        with pytest.raises(ValidationError):
            PersonaVersion.model_validate(fields)


def test_creator_reference_matches_database_bound() -> None:
    fields = version().model_dump()
    fields["creator_ref"] = "a" * 64
    assert PersonaVersion.model_validate(fields).creator_ref == "a" * 64
    fields["creator_ref"] = "a" * 65
    with pytest.raises(ValidationError):
        PersonaVersion.model_validate(fields)
