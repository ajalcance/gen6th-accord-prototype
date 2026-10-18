"""Bounded payloads cannot supply decision identity, roles or receipt fields."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.service import fingerprint
from accord.personas.workflow_contracts import ReviewCommand, WorkflowActor
from personas.workflow_fixtures import review_intent


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer_ref", "owner"),
        ("role", "reviewer"),
        ("recorded_at", "2026-10-01"),
        ("event_id", "f" * 32),
        ("fixture", False),
        ("decision", "AI_APPROVED"),
        ("statement", " "),
        ("statement", "x" * 501),
        ("version_id", "missing"),
        ("request_id", "missing"),
    ],
)
def test_review_intent_rejects_invalid_or_authoritative_inputs(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        review_intent(uuid4(), **{field: value})


def test_review_fingerprint_includes_previous_decision_and_version() -> None:
    intent = review_intent(uuid4())
    same = ReviewCommand.model_validate(intent.model_dump())
    assert fingerprint(intent) == fingerprint(same)
    for field, value in [
        ("version_id", uuid4()),
        ("expected_previous_id", uuid4()),
        ("decision", "changes_requested"),
        ("statement", "A different claim."),
    ]:
        changed = ReviewCommand.model_validate({**intent.model_dump(), field: value})
        assert fingerprint(intent) != fingerprint(changed)


def test_actor_context_is_bounded_and_cannot_grant_role() -> None:
    with pytest.raises(ValidationError):
        WorkflowActor.model_validate({"actor_ref": "a", "kind": "human", "role": "reviewer"})
    with pytest.raises(ValidationError):
        WorkflowActor(actor_ref="x" * 65, kind="human")
