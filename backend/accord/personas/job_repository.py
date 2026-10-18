"""Tenant/creator-bound jobs and serialized append-only state; no elevated worker role."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import FaceCommand
from accord.personas.face_repository import reference
from accord.personas.job_contracts import JobReceipt, JobState
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.repository import AccessDeniedError, authorize


async def job_lock(session: AsyncSession, workspace: UUID, job: UUID, *, wait: bool = True) -> None:
    name = "pg_advisory_xact_lock" if wait else "pg_try_advisory_xact_lock"
    value = await session.scalar(
        text(f"SELECT {name}(hashtextextended(:scope, 0))"),
        {"scope": f"accord-face-job:{workspace}:{job}"},
    )
    if not wait and value is not True:
        raise RuntimeError("job already processing")


async def latest(session: AsyncSession, row: FaceJob) -> FaceJobTransition:
    result = await session.scalar(
        select(FaceJobTransition)
        .where(
            FaceJobTransition.workspace_id == row.workspace_id,
            FaceJobTransition.job_id == row.id,
        )
        .order_by(FaceJobTransition.sequence.desc())
        .limit(1)
    )
    if result is None:
        raise RuntimeError("job has no committed state")
    return result


async def owned(session: AsyncSession, workspace: UUID, actor: str, job: UUID) -> FaceJob:
    await authorize(session, workspace, actor, write=True)
    row = await session.scalar(
        select(FaceJob).where(
            FaceJob.workspace_id == workspace,
            FaceJob.id == job,
            FaceJob.actor_ref == actor,
        )
    )
    if row is None:
        raise AccessDeniedError("face job access denied")
    await reference(session, workspace, actor, FaceCommand.model_validate(row.command), write=True)
    return row


def recoverable(event: FaceJobTransition, now: datetime) -> bool:
    if event.attempts >= 3 or event.sequence >= 29 or event.state in {"succeeded", "cancelled"}:
        return False
    if event.state == "failed":
        return True
    if event.state == "running":
        return event.lease_until is not None and now >= event.lease_until
    return now >= event.recorded_at + timedelta(minutes=2)


def receipt(row: FaceJob, event: FaceJobTransition) -> JobReceipt:
    return JobReceipt(
        job_id=row.id,
        workspace_id=row.workspace_id,
        version_id=row.version_id,
        portrait_id=row.portrait_id,
        command=FaceCommand.model_validate(row.command),
        state=cast(JobState, event.state),
        sequence=event.sequence,
        attempts=event.attempts,
        recorded_at=row.recorded_at,
        updated_at=event.recorded_at,
        lease_until=event.lease_until,
        generation_id=event.generation_id,
        recovery_available=recoverable(event, datetime.now(UTC)),
    )


def transition(
    session: AsyncSession,
    row: FaceJob,
    previous: FaceJobTransition | None,
    state: JobState,
    *,
    request: UUID | None = None,
    intent: str = "",
    generation: UUID | None = None,
) -> FaceJobTransition:
    now = datetime.now(UTC)
    event = FaceJobTransition(
        workspace_id=row.workspace_id,
        job_id=row.id,
        sequence=previous.sequence + 1 if previous else 0,
        request_id=request or uuid4(),
        fingerprint=hashlib.sha256(intent.encode()).hexdigest(),
        dispatch_id=(
            uuid4()
            if previous and state == "queued"
            else previous.dispatch_id if previous else row.id
        ),
        state=state,
        attempts=(previous.attempts if previous else 0) + (state == "running"),
        recorded_at=now,
        lease_until=now + timedelta(seconds=120) if state == "running" else None,
        generation_id=generation,
    )
    session.add(event)
    return event
