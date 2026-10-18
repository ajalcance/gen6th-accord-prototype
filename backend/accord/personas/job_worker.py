"""Authenticated task references execute stored authorized intent; SQL completion is atomic."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.face_contracts import FaceCommand
from accord.personas.face_service import process_in_transaction
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.job_repository import job_lock, latest, owned, transition
from accord.personas.job_runtime import JobRuntime
from accord.personas.job_service import dispatch_one, internal_row
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.task_google import TaskReference


def observation(session: AsyncSession, workspace: UUID, principal: str, operation: str) -> None:
    session.add(
        Event(
            event_id=uuid4().hex,
            ts=datetime.now(UTC),
            actor_type="system",
            actor_id=principal,
            tenant_id=workspace,
            category="persona",
            action="persona.workspace_observed",
            outcome="success",
            severity="info",
            source="server",
            metadata_={"operation": operation},
        )
    )


async def start(
    session: AsyncSession,
    ref: TaskReference,
    runtime: JobRuntime,
    principal: str,
) -> FaceJobTransition | None:
    async with session.begin():
        await job_lock(session, ref.workspace_id, ref.job_id, wait=False)
        row = await internal_row(session, ref.workspace_id, ref.job_id)
        event = await latest(session, row)
        if (
            event.dispatch_id != ref.dispatch_id
            or event.state in {"succeeded", "cancelled"}
            or event.attempts >= 3
        ):
            observation(session, ref.workspace_id, principal, "job_replay_observed")
            return None
        if event.lease_until is not None and datetime.now(UTC) < event.lease_until:
            raise RuntimeError("job lease still active")
        try:
            if row.config_id != runtime.config_id:
                raise AccessDeniedError("job configuration changed")
            await owned(session, ref.workspace_id, row.actor_ref, ref.job_id)
        except AccessDeniedError:
            transition(session, row, event, "cancelled")
            observation(session, ref.workspace_id, principal, "job_cancelled")
            return None
        running = transition(session, row, event, "running")
        observation(session, ref.workspace_id, principal, "job_started")
    return running


async def execute(
    session: AsyncSession,
    ref: TaskReference,
    runtime: JobRuntime,
    principal: str,
) -> None:
    if ref.workspace_id != runtime.workspace_id:
        raise AccessDeniedError("worker scope denied")
    running = await start(session, ref, runtime, principal)
    if running is None:
        return
    sequence = running.sequence
    try:
        async with asyncio.timeout(100):
            async with session.begin():
                await job_lock(session, ref.workspace_id, ref.job_id, wait=False)
                row = await internal_row(session, ref.workspace_id, ref.job_id)
                event = await latest(session, row)
                if event.sequence != sequence or event.dispatch_id != ref.dispatch_id:
                    observation(session, ref.workspace_id, principal, "job_superseded")
                    return
                result = await process_in_transaction(
                    session,
                    ref.workspace_id,
                    row.actor_ref,
                    FaceCommand.model_validate(row.command),
                    runtime.wrapper,
                    runtime.faces,
                )
                await session.flush()
                transition(session, row, event, "succeeded", generation=result.generation_id)
                observation(session, ref.workspace_id, principal, "job_succeeded")
    except Exception as exc:
        await fail(
            session,
            ref,
            sequence,
            principal,
            isinstance(exc, (AccessDeniedError, ConflictError)),
        )
        raise RuntimeError("job processing unavailable") from exc


async def fail(
    session: AsyncSession,
    ref: TaskReference,
    sequence: int,
    principal: str,
    denied: bool,
) -> None:
    async with session.begin():
        await job_lock(session, ref.workspace_id, ref.job_id)
        row = await internal_row(session, ref.workspace_id, ref.job_id)
        event = await latest(session, row)
        if event.sequence == sequence and event.state == "running":
            transition(session, row, event, "cancelled" if denied else "failed")
        observation(session, ref.workspace_id, principal, "job_failure_observed")


async def reconcile(session: AsyncSession, runtime: JobRuntime, principal: str) -> dict[str, int]:
    async with session.begin():
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :scope, true)"),
            {"scope": str(runtime.workspace_id)},
        )
        # Cursor is not needed: terminal/dispatched rows are excluded in SQL, not after LIMIT.
        last = (
            select(FaceJobTransition.state)
            .where(
                FaceJobTransition.workspace_id == FaceJob.workspace_id,
                FaceJobTransition.job_id == FaceJob.id,
            )
            .order_by(FaceJobTransition.sequence.desc())
            .limit(1)
            .scalar_subquery()
        )
        jobs = tuple(
            await session.scalars(
                select(FaceJob.id)
                .where(
                    FaceJob.workspace_id == runtime.workspace_id,
                    FaceJob.config_id == runtime.config_id,
                    last == "queued",
                )
                .order_by(FaceJob.recorded_at, FaceJob.id)
                .limit(20)
            )
        )
        observation(session, runtime.workspace_id, principal, "job_reconciliation_observed")
    count, examined = 0, 0
    try:
        async with asyncio.timeout(45):
            for job in jobs:
                examined += 1
                count += await dispatch_one(session, runtime.workspace_id, job, runtime)
    except TimeoutError:
        # Undispatched intents remain queued for a later authenticated reconciliation.
        pass
    return {"examined": examined, "dispatched": count}
