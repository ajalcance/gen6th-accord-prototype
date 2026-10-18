"""Minimal server decision events; no comments, conditions or private content."""

from datetime import datetime
from uuid import UUID

from accord.command.models import Event


def decision_event(
    *,
    workspace_id: UUID,
    actor_ref: str,
    request_id: UUID,
    record_id: UUID,
    version_id: UUID,
    event_id: str,
    recorded_at: datetime,
    action: str,
) -> Event:
    return Event(
        event_id=event_id,
        ts=recorded_at,
        actor_type="user",
        actor_id=actor_ref,
        tenant_id=workspace_id,
        category="persona",
        action=action,
        outcome="success",
        severity="info",
        resource_type="persona_decision",
        resource_id=str(record_id),
        correlation_id=str(request_id),
        source="server",
        metadata_={"version_id": str(version_id)},
    )
