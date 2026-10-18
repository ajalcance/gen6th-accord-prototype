"""Membership-scoped immutable version history with an observed bounded cursor."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.governance_contracts import VersionHistoryQuery, VersionPage
from accord.personas.models import Version
from accord.personas.repository import snapshot, version_row
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import authorize_actor


def observe_history(workspace: UUID, actor: WorkflowActor, request: UUID, version: UUID) -> Event:
    return decision_event(
        workspace_id=workspace,
        actor_ref=actor.actor_ref,
        request_id=request,
        record_id=version,
        version_id=version,
        event_id=uuid4().hex,
        recorded_at=datetime.now(UTC),
        action="persona.workflow_observed",
    )


async def version_history(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, query: VersionHistoryQuery
) -> VersionPage:
    request = uuid4()
    async with tracked_transaction(
        session, workspace, actor.actor_ref, request, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        head = await version_row(session, workspace, query.persona_id, None)
        statement = select(Version).where(
            Version.workspace_id == workspace, Version.persona_id == query.persona_id
        )
        if query.before_revision is not None:
            statement = statement.where(Version.revision < query.before_revision)
        rows = list(
            await session.scalars(
                statement.order_by(Version.revision.desc()).limit(query.limit + 1)
            )
        )
        items = tuple(snapshot(row) for row in rows[: query.limit])
        result = VersionPage(
            items=items,
            next_before_revision=items[-1].revision if len(rows) > query.limit else None,
        )
        session.add(observe_history(workspace, actor, request, head.id))
    return result
