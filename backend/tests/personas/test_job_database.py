"""Prepared owner/CI PostgreSQL acceptance: real SQL, encryption and atomic result replay."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import job_service, job_worker
from accord.personas.face_contracts import FaceCommand
from accord.personas.face_models import FaceGeneration
from accord.personas.job_contracts import JobUpdate
from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.job_repository import latest, transition
from accord.personas.job_runtime import JobRuntime
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from accord.personas.task_google import TaskReference
from personas.conftest import command
from personas.test_face_processing import SyntheticProviders
from personas.test_photo_storage import FixtureWrapper, staged
from personas.workflow_fixtures import human


async def setup_job(session: AsyncSession, workspace: UUID) -> tuple[FaceCommand, JobRuntime]:
    wrapper = FixtureWrapper()
    _, portrait = await staged(session, workspace, wrapper)
    version = await save(
        session, workspace, "creator-a", command(photo={"action": "attach", "upload_id": portrait})
    )
    intent = FaceCommand(version_id=version.version_id, portrait_id=portrait, request_id=uuid4())
    dispatcher = AsyncMock()
    dispatcher.dispatch.side_effect = RuntimeError("synthetic queue outage")
    runtime = JobRuntime(
        workspace, "a" * 64, wrapper, SyntheticProviders(()).providers(), dispatcher
    )
    return intent, runtime


@pytest.mark.asyncio
async def test_committed_queue_outage_reconciles_and_result_replays_once(
    session: AsyncSession, workspace: UUID
) -> None:
    intent, runtime = await setup_job(session, workspace)
    queued = await job_service.enqueue(session, workspace, human("creator-a"), intent, runtime)
    assert queued.state == "queued"
    assert isinstance(runtime.dispatcher, AsyncMock)
    runtime.dispatcher.dispatch.side_effect = None
    reconciled = await job_worker.reconcile(session, runtime, "synthetic-workload")
    assert reconciled == {"examined": 1, "dispatched": 1}
    ref = TaskReference(workspace_id=workspace, job_id=queued.job_id, dispatch_id=queued.job_id)
    await job_worker.execute(session, ref, runtime, "synthetic-workload")
    await job_worker.execute(session, ref, runtime, "synthetic-workload")
    result = await job_service.enqueue(session, workspace, human("creator-a"), intent, runtime)
    assert result.state == "succeeded" and result.attempts == 1
    async with session.begin():
        assert await session.scalar(select(func.count()).select_from(FaceGeneration)) == 1


@pytest.mark.asyncio
async def test_creator_and_active_reference_intents_are_bound(
    session: AsyncSession, workspace: UUID
) -> None:
    intent, runtime = await setup_job(session, workspace)
    await job_service.enqueue(session, workspace, human("creator-a"), intent, runtime)
    with pytest.raises(AccessDeniedError):
        await job_service.enqueue(session, workspace, human("creator-b"), intent, runtime)
    with pytest.raises(ConflictError):
        await job_service.enqueue(
            session,
            workspace,
            human("creator-a"),
            intent.model_copy(update={"request_id": uuid4()}),
            runtime,
        )
    with pytest.raises(ConflictError):
        await job_service.update(
            session,
            workspace,
            human("creator-a"),
            JobUpdate(
                job_id=intent.request_id, request_id=uuid4(), expected_sequence=1, action="cancel"
            ),
            runtime,
        )


@pytest.mark.asyncio
async def test_cancelled_job_never_calls_provider_and_cannot_append_terminal_state(
    session: AsyncSession, workspace: UUID
) -> None:
    intent, runtime = await setup_job(session, workspace)
    queued = await job_service.enqueue(session, workspace, human("creator-a"), intent, runtime)
    cancelled = await job_service.update(
        session,
        workspace,
        human("creator-a"),
        JobUpdate(job_id=queued.job_id, request_id=uuid4(), expected_sequence=0, action="cancel"),
        runtime,
    )
    await job_worker.execute(
        session,
        TaskReference(workspace_id=workspace, job_id=queued.job_id, dispatch_id=queued.job_id),
        runtime,
        "synthetic-workload",
    )
    assert cancelled.state == "cancelled"
    async with session.begin():
        assert await session.scalar(select(func.count()).select_from(FaceGeneration)) == 0
        row = await session.get(FaceJob, queued.job_id)
        assert row is not None
        event = await latest(session, row)
        with pytest.raises(DBAPIError, match="invalid job sequence"):
            async with session.begin_nested():
                transition(session, row, event, "running")
                await session.flush()
        with pytest.raises(DBAPIError):
            async with session.begin_nested():
                await session.execute(text("UPDATE persona_face_jobs SET actor_ref = 'changed'"))


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_field", ["sequence", "attempts"])
async def test_raw_invalid_transition_sequence_is_rejected(
    session: AsyncSession, workspace: UUID, invalid_field: str
) -> None:
    intent, runtime = await setup_job(session, workspace)
    await job_service.enqueue(session, workspace, human("creator-a"), intent, runtime)
    async with session.begin():
        row = await session.get(FaceJob, intent.request_id)
        assert row is not None
        previous = await latest(session, row)
        with pytest.raises(DBAPIError, match="invalid job sequence"):
            async with session.begin_nested():
                event = transition(session, row, previous, "running")
                if invalid_field == "sequence":
                    event.sequence = 5
                else:
                    event.attempts = previous.attempts
                await session.flush()
        assert await session.scalar(select(func.count()).select_from(FaceJobTransition)) == 1


@pytest.mark.asyncio
async def test_worker_failure_and_retry_outage_preserve_committed_state(
    session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    intent, runtime = await setup_job(session, workspace)
    queued = await job_service.enqueue(session, workspace, human("creator-a"), intent, runtime)
    process = AsyncMock(side_effect=RuntimeError("synthetic provider outage"))
    monkeypatch.setattr(job_worker, "process_in_transaction", process)
    with pytest.raises(RuntimeError, match="job processing unavailable"):
        await job_worker.execute(
            session,
            TaskReference(workspace_id=workspace, job_id=queued.job_id, dispatch_id=queued.job_id),
            runtime,
            "synthetic-workload",
        )
    failed = await job_service.inspect(session, workspace, human("creator-a"), queued.job_id)
    assert failed.state == "failed" and failed.attempts == 1 and failed.sequence == 2
    retry = JobUpdate(
        job_id=queued.job_id, request_id=uuid4(), expected_sequence=failed.sequence, action="retry"
    )
    recovered = await job_service.update(session, workspace, human("creator-a"), retry, runtime)
    assert recovered.state == "queued" and recovered.attempts == 1 and recovered.sequence == 3
    assert (
        await job_service.update(session, workspace, human("creator-a"), retry, runtime)
        == recovered
    )
    process.assert_awaited_once()
