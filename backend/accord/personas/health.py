"""Workspace-scoped audit backlog observation; internal, not a public health route."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import AUDITABLE_ACTIONS
from accord.command.models import AuditLog, Event
from accord.personas.repository import authorize
from accord.personas.transactions import tracked_transaction


class AuditBacklog(BaseModel):
    """Operational counts, excluding the observation's own subsequent event."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    observation_request_id: UUID
    observed_at: datetime
    pending_events: int = Field(ge=0, strict=True)
    oldest_pending_at: datetime | None

    @field_validator("observed_at", "oldest_pending_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("observation timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def require_consistent_oldest(self) -> "AuditBacklog":
        if (self.pending_events == 0) != (self.oldest_pending_at is None):
            raise ValueError("oldest timestamp must correspond to a nonempty backlog")
        return self


async def observe_backlog(
    session: AsyncSession, workspace_id: UUID, actor_ref: str
) -> AuditBacklog:
    """Authorize, aggregate in one SQL snapshot, and durably record the observation."""
    request_id = uuid4()
    async with tracked_transaction(session, workspace_id, actor_ref, request_id):
        await authorize(session, workspace_id, actor_ref, write=False)
        sealed = exists().where(
            AuditLog.event_id == Event.event_id, AuditLog.tenant_id == workspace_id
        )
        query = select(func.count(Event.event_id), func.min(Event.ts)).where(
            Event.tenant_id == workspace_id,
            Event.category == "persona",
            Event.source == "server",
            Event.action.in_(AUDITABLE_ACTIONS),
            ~sealed,
        )
        count, oldest = (await session.execute(query)).one()
        result = AuditBacklog(
            workspace_id=workspace_id,
            observation_request_id=request_id,
            observed_at=datetime.now(UTC),
            pending_events=count,
            oldest_pending_at=oldest,
        )
        session.add(observation_event(result, actor_ref))
    return result


def observation_event(result: AuditBacklog, actor_ref: str) -> Event:
    return Event(
        event_id=uuid4().hex,
        ts=result.observed_at,
        actor_type="user",
        actor_id=actor_ref,
        tenant_id=result.workspace_id,
        category="persona",
        action="persona.workspace_observed",
        outcome="success",
        severity="info",
        source="server",
        correlation_id=str(result.observation_request_id),
        metadata_={"pending_events": result.pending_events},
    )
