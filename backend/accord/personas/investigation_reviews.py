"""Save an exact-version handoff; existing independent review owns human decisions."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.investigation_contracts import InvestigationHistory
from accord.personas.investigation_models import InvestigationRecord
from accord.personas.investigation_review_contracts import (
    InvestigationReviewCommand,
    InvestigationReviewPage,
    InvestigationReviewReceipt,
)
from accord.personas.investigation_review_models import InvestigationReviewRequest
from accord.personas.photo_storage import photo_event
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.similarity_service import observation
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, locked_version, require_current


def receipt(row: InvestigationReviewRequest) -> InvestigationReviewReceipt:
    return InvestigationReviewReceipt.model_validate(
        {
            field: getattr(row, field)
            for field in InvestigationReviewReceipt.model_fields
            if field != "state"
        }
    )


async def requests(
    session: AsyncSession, workspace: UUID, query: InvestigationHistory
) -> list[InvestigationReviewRequest]:
    statement = select(InvestigationReviewRequest).where(
        InvestigationReviewRequest.workspace_id == workspace,
        InvestigationReviewRequest.version_id == query.version_id,
    )
    if query.before_ordinal is not None:
        statement = statement.where(InvestigationReviewRequest.ordinal < query.before_ordinal)
    return list(
        await session.scalars(
            statement.order_by(InvestigationReviewRequest.ordinal.desc()).limit(21)
        )
    )


async def prior_request(
    session: AsyncSession, workspace: UUID, actor: str, command: InvestigationReviewCommand
) -> InvestigationReviewRequest | None:
    row = await session.scalar(
        select(InvestigationReviewRequest).where(
            InvestigationReviewRequest.workspace_id == workspace,
            InvestigationReviewRequest.requester_ref == actor,
            InvestigationReviewRequest.request_id == command.request_id,
        )
    )
    if row is not None and (
        row.version_id != command.version_id or row.investigation_id != command.investigation_id
    ):
        raise ConflictError("review request reused with different evidence")
    return row


async def request_review(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationReviewCommand,
) -> InvestigationReviewReceipt:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        version, persona = await locked_version(session, workspace, command.version_id)
        prior = await prior_request(session, workspace, actor.actor_ref, command)
        if prior is None:
            require_current(version, persona)
            prior = await append_request(session, workspace, actor, command)
        result = receipt(prior)
        await authorize_actor(session, workspace, actor, None)
        observation(session, workspace, actor, command.request_id)
    return result


async def append_request(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: InvestigationReviewCommand,
) -> InvestigationReviewRequest:
    packet = await session.scalar(
        select(InvestigationRecord).where(
            InvestigationRecord.workspace_id == workspace,
            InvestigationRecord.version_id == command.version_id,
            InvestigationRecord.id == command.investigation_id,
        )
    )
    if packet is None:
        raise AccessDeniedError("investigation review evidence denied")
    rows = await requests(session, workspace, InvestigationHistory(version_id=command.version_id))
    row = InvestigationReviewRequest(
        id=uuid4(),
        workspace_id=workspace,
        version_id=command.version_id,
        investigation_id=command.investigation_id,
        request_id=command.request_id,
        ordinal=rows[0].ordinal + 1 if rows else 1,
        requester_ref=actor.actor_ref,
        requested_at=datetime.now(UTC),
    )
    session.add(row)
    event = photo_event(
        "persona.workspace_observed", workspace, actor.actor_ref, row.id, command.request_id
    )
    event.actor_type, event.resource_type = actor.audit_type, "persona_investigation_review"
    event.metadata_ = {"operation": "investigation_review_requested"}
    session.add(event)
    await session.flush()
    return row


async def history(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: InvestigationHistory
) -> InvestigationReviewPage:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        await locked_version(session, workspace, command.version_id)
        rows = await requests(session, workspace, command)
        items = tuple(receipt(row) for row in rows[:20])
        await authorize_actor(session, workspace, actor, None)
        result = InvestigationReviewPage(
            workspace_id=workspace,
            version_id=command.version_id,
            items=items,
            next_before_ordinal=items[-1].ordinal if len(rows) > 20 else None,
        )
        observation(session, workspace, actor, uuid4())
    return result
