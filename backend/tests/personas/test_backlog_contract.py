"""Pure operational observation contracts do not establish live monitoring."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accord.personas.health import AuditBacklog, observation_event


def backlog(**changes: object) -> AuditBacklog:
    return AuditBacklog.model_validate(
        {
            "workspace_id": uuid4(),
            "observation_request_id": uuid4(),
            "observed_at": datetime.now(UTC),
            "pending_events": 0,
            "oldest_pending_at": None,
            **changes,
        }
    )


@pytest.mark.parametrize("count", [-1, True, "1"])
def test_invalid_count_is_rejected(count: object) -> None:
    with pytest.raises(ValidationError):
        backlog(pending_events=count)


@pytest.mark.parametrize("field", ["observed_at", "oldest_pending_at"])
def test_ambiguous_time_is_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        backlog(**{field: datetime(2026, 10, 1)})


@pytest.mark.parametrize(
    "changes", [{"pending_events": 1}, {"oldest_pending_at": datetime.now(UTC)}]
)
def test_contradictory_count_and_oldest_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        backlog(**changes)


def test_observation_is_minimal_server_event() -> None:
    snapshot = backlog(pending_events=2, oldest_pending_at=datetime.now(UTC))
    event = observation_event(snapshot, "viewer")
    assert event.source == "server" and event.actor_id == "viewer"
    assert event.tenant_id == snapshot.workspace_id
    assert event.correlation_id == str(snapshot.observation_request_id)
    assert event.metadata_ == {"pending_events": 2}
    assert event.ts == snapshot.observed_at
