"""Commit intent before task creation; explicit recovery never erases durable history."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import FaceCommand, FaceSubject
from accord.personas.face_repository import generation, reference
from accord.personas.face_storage import command_fingerprint
from accord.personas.job_contracts import JobPage, JobReceipt, JobUpdate
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.job_repository import job_lock, latest, owned, receipt, recoverable, transition
from accord.personas.job_runtime import JobRuntime
from accord.personas.passport_repository import observation
from accord.personas.repository import AccessDeniedError, ConflictError, authorize
from accord.personas.task_google import TaskReference
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor


def available(workspace: UUID, runtime: JobRuntime | None) -> JobRuntime:
    if runtime is None or runtime.workspace_id != workspace:
        raise RuntimeError("durable processing unavailable")
    return runtime


async def enqueue(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: FaceCommand,
    runtime: JobRuntime | None,
) -> JobReceipt:
    async with tracked_transaction(session, workspace, actor.actor_ref, command.request_id):
        await authorize(session, workspace, actor.actor_ref, write=True)
        configured = available(workspace, runtime)
        await job_lock(session, workspace, command.request_id)
        await reference(session, workspace, actor.actor_ref, command, write=True)
        row = await session.scalar(
            select(FaceJob).where(
                FaceJob.workspace_id == workspace,
                FaceJob.request_id == command.request_id,
            )
        )
        if row is not None:
            if row.actor_ref != actor.actor_ref or row.fingerprint != command_fingerprint(command):
                raise ConflictError("job request reused with different intent")
        else:
            await require_idle_reference(session, workspace, command)
            if (
                command.generation_id
                and await generation(session, workspace, command, identity=command.generation_id)
                is None
            ):
                raise AccessDeniedError("selected generation unavailable")
            row = FaceJob(
                id=command.request_id,
                workspace_id=workspace,
                version_id=command.version_id,
                portrait_id=command.portrait_id,
                request_id=command.request_id,
                actor_ref=actor.actor_ref,
                config_id=configured.config_id,
                fingerprint=command_fingerprint(command),
                command=command.model_dump(mode="json"),
                recorded_at=datetime.now(UTC),
            )
            session.add(row)
            await session.flush()
            transition(session, row, None, "queued")
        observation(session, workspace, actor, row.id, row.version_id)
        job_id = row.id
    await dispatch_one(session, workspace, job_id, configured)
    return await inspect(session, workspace, actor, job_id)


async def require_idle_reference(
    session: AsyncSession,
    workspace: UUID,
    subject: FaceSubject,
) -> None:
    state = (
        select(FaceJobTransition.state)
        .where(
            FaceJobTransition.workspace_id == FaceJob.workspace_id,
            FaceJobTransition.job_id == FaceJob.id,
        )
        .order_by(FaceJobTransition.sequence.desc())
        .limit(1)
        .scalar_subquery()
    )
    attempts = (
        select(FaceJobTransition.attempts)
        .where(
            FaceJobTransition.workspace_id == FaceJob.workspace_id,
            FaceJobTransition.job_id == FaceJob.id,
        )
        .order_by(FaceJobTransition.sequence.desc())
        .limit(1)
        .scalar_subquery()
    )
    active = await session.scalar(
        select(FaceJob.id)
        .where(
            FaceJob.workspace_id == workspace,
            FaceJob.version_id == subject.version_id,
            FaceJob.portrait_id == subject.portrait_id,
            state.not_in(("succeeded", "cancelled")),
            attempts < 3,
        )
        .limit(1)
    )
    if active is not None:
        raise ConflictError("reference already has pending work")


async def inspect(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    job: UUID,
) -> JobReceipt:
    async with tracked_transaction(session, workspace, actor.actor_ref, uuid4()):
        row = await owned(session, workspace, actor.actor_ref, job)
        result = receipt(row, await latest(session, row))
        await authorize(session, workspace, actor.actor_ref, write=True)
        observation(session, workspace, actor, row.id, row.version_id)
    return result


async def history(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    subject: FaceSubject,
) -> JobPage:
    async with tracked_transaction(session, workspace, actor.actor_ref, uuid4()):
        await authorize(session, workspace, actor.actor_ref, write=True)
        await reference(session, workspace, actor.actor_ref, subject, write=True)
        rows = tuple(
            await session.scalars(
                select(FaceJob)
                .where(
                    FaceJob.workspace_id == workspace,
                    FaceJob.actor_ref == actor.actor_ref,
                    FaceJob.version_id == subject.version_id,
                    FaceJob.portrait_id == subject.portrait_id,
                )
                .order_by(FaceJob.recorded_at.desc(), FaceJob.id.desc())
                .limit(21)
            )
        )
        items = tuple([receipt(row, await latest(session, row)) for row in rows[:20]])
        await authorize(session, workspace, actor.actor_ref, write=True)
        observation(session, workspace, actor, subject.portrait_id, subject.version_id)
        result = JobPage(
            workspace_id=workspace, **subject.model_dump(), items=items, overflow=len(rows) > 20
        )
    return result


async def update(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: JobUpdate,
    runtime: JobRuntime | None,
) -> JobReceipt:
    async with tracked_transaction(session, workspace, actor.actor_ref, command.request_id):
        await authorize(session, workspace, actor.actor_ref, write=True)
        await job_lock(session, workspace, command.job_id)
        row = await owned(session, workspace, actor.actor_ref, command.job_id)
        event = await latest(session, row)
        prior = await session.scalar(
            select(FaceJobTransition).where(
                FaceJobTransition.workspace_id == workspace,
                FaceJobTransition.request_id == command.request_id,
            )
        )
        if prior is not None:
            if (
                prior.job_id != row.id
                or prior.fingerprint
                != hashlib.sha256(command.model_dump_json().encode()).hexdigest()
            ):
                raise ConflictError("job update intent changed")
        else:
            if event.sequence != command.expected_sequence or event.state in {
                "succeeded",
                "cancelled",
            }:
                raise ConflictError("job state changed")
            if command.action == "retry":
                configured = available(workspace, runtime)
                if row.config_id != configured.config_id or not recoverable(
                    event, datetime.now(UTC)
                ):
                    raise ConflictError("job cannot be retried with this configuration")
            transition(
                session,
                row,
                event,
                "queued" if command.action == "retry" else "cancelled",
                request=command.request_id,
                intent=command.model_dump_json(),
            )
        observation(session, workspace, actor, row.id, row.version_id)
    if command.action == "retry":
        await dispatch_one(session, workspace, command.job_id, available(workspace, runtime))
    return await inspect(session, workspace, actor, command.job_id)


async def dispatch_one(
    session: AsyncSession,
    workspace: UUID,
    job: UUID,
    runtime: JobRuntime,
) -> bool:
    try:
        async with session.begin():
            row = await internal_row(session, workspace, job)
            await job_lock(session, workspace, job, wait=False)
            event = await latest(session, row)
            if event.state != "queued" or row.config_id != runtime.config_id:
                return False
            await owned(session, workspace, row.actor_ref, job)
            await runtime.dispatcher.dispatch(
                TaskReference(
                    workspace_id=workspace,
                    job_id=job,
                    dispatch_id=event.dispatch_id,
                )
            )
            await authorize(session, workspace, row.actor_ref, write=True)
            transition(session, row, event, "dispatched")
        return True
    except Exception:
        return False


async def internal_row(session: AsyncSession, workspace: UUID, job: UUID) -> FaceJob:
    await session.execute(
        text("SELECT set_config('accord.workspace_id', :scope, true)"), {"scope": str(workspace)}
    )
    row = await session.scalar(
        select(FaceJob).where(FaceJob.workspace_id == workspace, FaceJob.id == job)
    )
    if row is None:
        raise AccessDeniedError("job unavailable")
    return row
