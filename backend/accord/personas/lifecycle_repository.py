"""Scoped lifecycle queries; callers hold the performer lock in an authorised transaction."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.lifecycle_contracts import LifecycleReceipt
from accord.personas.lifecycle_models import LifecycleRecord
from accord.personas.photo_storage import photo_event
from accord.personas.repository import ConflictError
from accord.personas.workflow_contracts import WorkflowActor


def observe(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    request: UUID,
    record: UUID,
    operation: str,
) -> None:
    event = photo_event("persona.workspace_observed", workspace, actor.actor_ref, record, request)
    event.actor_type, event.resource_type = actor.audit_type, "persona_lifecycle_record"
    event.metadata_ = {"operation": operation}
    session.add(event)


def receipt(row: LifecycleRecord) -> LifecycleReceipt:
    return LifecycleReceipt.model_validate(
        {field: getattr(row, field) for field in LifecycleReceipt.model_fields}
    )


async def latest(
    session: AsyncSession,
    workspace: UUID,
    persona: UUID,
    kind: str | None = None,
    version: UUID | None = None,
    target: UUID | None = None,
    requirement: str | None = None,
) -> LifecycleRecord | None:
    query = select(LifecycleRecord).where(
        LifecycleRecord.workspace_id == workspace, LifecycleRecord.persona_id == persona
    )
    for column, value in (
        (LifecycleRecord.kind, kind),
        (LifecycleRecord.version_id, version),
        (LifecycleRecord.target_id, target),
        (LifecycleRecord.requirement, requirement),
    ):
        if value is not None:
            query = query.where(column == value)
    result: LifecycleRecord | None = await session.scalar(
        query.order_by(LifecycleRecord.ordinal.desc()).limit(1)
    )
    return result


async def replay(
    session: AsyncSession, workspace: UUID, actor: str, request: UUID, fingerprint: str
) -> LifecycleRecord | None:
    row = await session.scalar(
        select(LifecycleRecord).where(
            LifecycleRecord.workspace_id == workspace,
            LifecycleRecord.actor_ref == actor,
            LifecycleRecord.request_id == request,
        )
    )
    if row is not None and row.fingerprint != fingerprint:
        raise ConflictError("lifecycle request reused with different content")
    return row


async def target_record(
    session: AsyncSession, workspace: UUID, persona: UUID, target: UUID, kind: str
) -> LifecycleRecord:
    row = await session.scalar(
        select(LifecycleRecord).where(
            LifecycleRecord.workspace_id == workspace,
            LifecycleRecord.persona_id == persona,
            LifecycleRecord.id == target,
            LifecycleRecord.kind == kind,
        )
    )
    if row is None:
        raise ConflictError("lifecycle target is unavailable")
    return row


async def is_suspended(session: AsyncSession, workspace: UUID, persona: UUID) -> bool:
    report = LifecycleRecord.__table__.alias("report")
    response = LifecycleRecord.__table__.alias("response")
    current = (
        select(response.c.content["decision"].astext)
        .where(
            response.c.workspace_id == workspace,
            response.c.persona_id == persona,
            response.c.kind == "response",
            response.c.target_id == report.c.id,
        )
        .order_by(response.c.ordinal.desc())
        .limit(1)
        .correlate(report)
        .scalar_subquery()
    )
    return (
        await session.scalar(
            select(report.c.id)
            .where(
                report.c.workspace_id == workspace,
                report.c.persona_id == persona,
                report.c.kind == "concern",
                current == "suspended",
            )
            .limit(1)
        )
        is not None
    )
