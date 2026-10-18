"""Decision evidence must fail closed on mismatched attribution and references."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.command.audit import GENESIS_HASH, _entry_from_event
from accord.command.models import AuditLog, Event
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_evidence import validate_decision_reference
from accord.personas.workflow_evidence_contracts import DecisionAnchor, WorkflowEvidence


def anchor_fixture() -> DecisionAnchor:
    return DecisionAnchor(
        record_id=uuid4(),
        workspace_id=uuid4(),
        version_id=uuid4(),
        action="persona.review_recorded",
        actor_ref="reviewer-a",
        recorded_at=datetime.now(UTC),
        write_request_id=uuid4(),
        event_id=uuid4().hex,
    )


def reference_fixture(anchor: DecisionAnchor, kind: str) -> Event | AuditLog:
    event = decision_event(
        workspace_id=anchor.workspace_id,
        actor_ref=anchor.actor_ref,
        request_id=anchor.write_request_id,
        record_id=anchor.record_id,
        version_id=anchor.version_id,
        event_id=anchor.event_id,
        recorded_at=anchor.recorded_at,
        action=anchor.action,
    )
    return event if kind == "event" else _entry_from_event(event, GENESIS_HASH)


@pytest.mark.parametrize("kind", ["event", "audit"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("event_id", uuid4().hex),
        ("tenant_id", uuid4()),
        ("action", "persona.campaign_offered"),
        ("actor_type", "system"),
        ("actor_id", "creator-a"),
        ("outcome", "denied"),
        ("severity", "warn"),
        ("ts", datetime.now(UTC) + timedelta(days=1)),
        ("resource_type", "persona"),
        ("resource_id", str(uuid4())),
        ("metadata_", {"version_id": str(uuid4())}),
        ("metadata_", {"statement": "Private content"}),
    ],
)
def test_reference_rejects_mismatched_decision_fields(kind: str, field: str, value: object) -> None:
    anchor = anchor_fixture()
    row = reference_fixture(anchor, kind)
    validate_decision_reference(row, anchor)
    setattr(row, field, value)
    with pytest.raises(RuntimeError, match="references disagree"):
        validate_decision_reference(row, anchor)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "client"),
        ("category", "different"),
        ("correlation_id", str(uuid4())),
    ],
)
def test_cold_event_requires_server_source_and_exact_request(field: str, value: object) -> None:
    anchor = anchor_fixture()
    event = reference_fixture(anchor, "event")
    setattr(event, field, value)
    with pytest.raises(RuntimeError, match="server observation"):
        validate_decision_reference(event, anchor)


@pytest.mark.parametrize(
    "changes",
    [
        {"cold_event_present": False},
        {"cold_event_present": 1},
        {"audit_state": "entry_present"},
        {"audit_sequence": 1},
        {"audit_entry_hash": "a" * 64},
        {"audit_sequence": 0},
        {"audit_entry_hash": "invalid"},
    ],
)
def test_evidence_rejects_contradictory_or_invalid_presence(changes: dict[str, object]) -> None:
    fixture = {
        "anchor": anchor_fixture(),
        "observation_request_id": uuid4(),
        "cold_event_present": True,
        "audit_state": "pending",
        "audit_sequence": None,
        "audit_entry_hash": None,
    }
    assert WorkflowEvidence.model_validate(fixture).audit_state == "pending"
    with pytest.raises(ValidationError):
        WorkflowEvidence.model_validate({**fixture, **changes})


def test_audit_only_presence_is_explicit_and_requires_aware_record_time() -> None:
    anchor = anchor_fixture()
    result = WorkflowEvidence(
        anchor=anchor,
        observation_request_id=uuid4(),
        cold_event_present=False,
        audit_state="entry_present",
        audit_sequence=1,
        audit_entry_hash="a" * 64,
    )
    assert not result.cold_event_present and result.audit_state == "entry_present"
    with pytest.raises(ValidationError, match="timezone"):
        DecisionAnchor.model_validate({**anchor.model_dump(), "recorded_at": datetime(2026, 10, 1)})
