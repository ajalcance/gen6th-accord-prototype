"""Minimal server observation of an atomic detection batch, without recursion."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from accord.command.models import Event


def batch_event(workspace: UUID, count: int, digest: str) -> Event:
    return Event(
        event_id=uuid4().hex,
        tenant_id=workspace,
        ts=datetime.now(UTC),
        actor_type="system",
        category="command",
        action="command.persona_detection_evaluated",
        outcome="success",
        severity="info",
        source="server",
        metadata_={"evaluated_events": count, "rules_digest": digest},
    )
