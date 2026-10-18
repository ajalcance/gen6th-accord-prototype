"""Authorized aggregate detection diagnostics; never expose another tenant's findings."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.detection import PERSONA_ACTIONS
from accord.command.detection_models import DetectionReceipt
from accord.command.models import Event
from accord.personas.health import AuditBacklog, observation_event
from accord.personas.repository import authorize
from accord.personas.transactions import tracked_transaction


async def observe_detection_backlog(
    session: AsyncSession, workspace_id: UUID, actor_ref: str
) -> AuditBacklog:
    """Reuse the bounded count/oldest contract and registered observation action."""
    request_id = uuid4()
    async with tracked_transaction(session, workspace_id, actor_ref, request_id):
        await authorize(session, workspace_id, actor_ref, write=False)
        evaluated = exists().where(
            DetectionReceipt.event_id == Event.event_id,
            DetectionReceipt.workspace_id == workspace_id,
        )
        count, oldest = (
            await session.execute(
                select(func.count(Event.event_id), func.min(Event.ts)).where(
                    Event.tenant_id == workspace_id,
                    Event.source == "server",
                    Event.category == "persona",
                    Event.action.in_(PERSONA_ACTIONS),
                    ~evaluated,
                )
            )
        ).one()
        result = AuditBacklog(
            workspace_id=workspace_id,
            observation_request_id=request_id,
            observed_at=datetime.now(UTC),
            pending_events=count,
            oldest_pending_at=oldest,
        )
        event = observation_event(result, actor_ref)
        event.metadata_ = {"pending_detection_events": count}
        session.add(event)
    return result
