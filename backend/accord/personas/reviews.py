"""Complete internal review transitions; no routes or model approval path."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.review_models import ReviewRecord
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import (
    ReviewCommand,
    ReviewHistoryQuery,
    ReviewPage,
    ReviewSnapshot,
    WorkflowActor,
)
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import (
    authorize_actor,
    latest_review,
    locked_version,
    require_current,
)


def review_snapshot(row: ReviewRecord) -> ReviewSnapshot:
    return ReviewSnapshot.model_validate(
        {field: getattr(row, field) for field in ReviewSnapshot.model_fields}
    )


async def _replay(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, command: ReviewCommand
) -> ReviewRecord | None:
    row = await session.scalar(
        select(ReviewRecord).where(
            ReviewRecord.workspace_id == workspace_id,
            ReviewRecord.reviewer_ref == actor_ref,
            ReviewRecord.request_id == command.request_id,
        )
    )
    if row is not None and row.fingerprint != fingerprint(command):
        raise ConflictError("review request ID already used for different content")
    return row


async def _append(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, command: ReviewCommand
) -> ReviewRecord:
    previous = await latest_review(session, workspace_id, command.version_id)
    if (previous.id if previous else None) != command.expected_previous_id:
        raise ConflictError("review decision changed")
    row = ReviewRecord(
        id=uuid4(),
        workspace_id=workspace_id,
        version_id=command.version_id,
        ordinal=previous.ordinal + 1 if previous else 1,
        reviewer_ref=actor_ref,
        request_id=command.request_id,
        fingerprint=fingerprint(command),
        decision=command.decision,
        statement=command.statement,
        recorded_at=datetime.now(UTC),
        event_id=uuid4().hex,
    )
    session.add(
        decision_event(
            workspace_id=workspace_id,
            actor_ref=actor_ref,
            request_id=command.request_id,
            record_id=row.id,
            version_id=row.version_id,
            event_id=row.event_id,
            recorded_at=row.recorded_at,
            action="persona.review_recorded",
        )
    )
    session.add(row)
    await session.flush()
    return row


async def record_review(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, command: ReviewCommand
) -> ReviewSnapshot:
    """Authorize afresh, serialize with edits, append decision and event atomically."""
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, "reviewer")
        version, persona = await locked_version(session, workspace_id, command.version_id)
        if actor.actor_ref == persona.owner_ref or actor.actor_ref == version.creator_ref:
            raise AccessDeniedError("self-review is not permitted")
        row = await _replay(session, workspace_id, actor.actor_ref, command)
        if row is None:
            require_current(version, persona)
            row = await _append(session, workspace_id, actor.actor_ref, command)
        result = review_snapshot(row)
    return result


async def review_history(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, query: ReviewHistoryQuery
) -> ReviewPage:
    """Bounded newest-first history; retries return receipts, not current approval status."""
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, None)
        await locked_version(session, workspace_id, query.version_id)
        statement = select(ReviewRecord).where(
            ReviewRecord.workspace_id == workspace_id, ReviewRecord.version_id == query.version_id
        )
        if query.before_ordinal is not None:
            statement = statement.where(ReviewRecord.ordinal < query.before_ordinal)
        rows = list(
            await session.scalars(
                statement.order_by(ReviewRecord.ordinal.desc()).limit(query.limit + 1)
            )
        )
        items = tuple(review_snapshot(row) for row in rows[: query.limit])
        result = ReviewPage(
            items=items,
            next_before_ordinal=(items[-1].ordinal if len(rows) > query.limit else None),
        )
        session.add(
            decision_event(
                workspace_id=workspace_id,
                actor_ref=actor.actor_ref,
                request_id=request_id,
                record_id=query.version_id,
                version_id=query.version_id,
                event_id=uuid4().hex,
                recorded_at=datetime.now(UTC),
                action="persona.workflow_observed",
            )
        )
    return result
