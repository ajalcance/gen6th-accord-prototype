"""Receipt presence states must be internally consistent without making trust claims."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.observability import PersistenceEvidence


def evidence(**changes: object) -> PersistenceEvidence:
    return PersistenceEvidence.model_validate(
        {
            "workspace_id": uuid4(),
            "persona_id": uuid4(),
            "version_id": uuid4(),
            "revision": 1,
            "recorded_at": datetime.now(UTC),
            "write_request_id": uuid4(),
            "observation_request_id": uuid4(),
            "event_id": uuid4().hex,
            "cold_event_present": True,
            "audit_state": "pending",
            "audit_sequence": None,
            "audit_entry_hash": None,
            **changes,
        }
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"audit_sequence": 1},
        {"audit_entry_hash": "a" * 64},
        {"audit_state": "entry_present"},
        {"cold_event_present": False},
        {"event_id": "invalid"},
        {"revision": 0},
        {"revision": True},
        {"recorded_at": datetime(2026, 10, 1)},
    ],
)
def test_contradictory_or_invalid_evidence_is_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        evidence(**changes)


def test_pending_and_retained_audit_entry_are_distinct_states() -> None:
    assert evidence().audit_state == "pending"
    recorded = evidence(
        audit_state="entry_present",
        audit_sequence=1,
        audit_entry_hash="a" * 64,
        cold_event_present=False,
    )
    assert recorded.audit_state == "entry_present" and not recorded.cold_event_present
