"""Intent-before-dispatch, CAS recovery, membership and bounded catalogue query proofs."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import job_service
from accord.personas.face_contracts import FaceCommand
from accord.personas.job_contracts import JobUpdate
from accord.personas.job_models import FaceJob
from accord.personas.job_repository import receipt, recoverable
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.workflow_contracts import WorkflowActor
from personas.job_test_support import prepare, runtime
from personas.runtime_fixtures import job_rows


@pytest.mark.asyncio
async def test_new_intent_is_committed_before_dispatch_and_survives_queue_outage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, initial = job_rows()
    actor = WorkflowActor(actor_ref=row.actor_ref, kind="human")
    async with AsyncSession() as session:
        prepare(monkeypatch, session, row, initial)
        add = Mock()
        monkeypatch.setattr(session, "add", add)
        monkeypatch.setattr(session, "scalar", AsyncMock(return_value=None))

        async def dispatch(*args: object) -> bool:
            assert not session.in_transaction()
            assert any(isinstance(call.args[0], FaceJob) for call in add.call_args_list)
            return False

        monkeypatch.setattr(job_service, "dispatch_one", dispatch)
        result = await job_service.enqueue(
            session, row.workspace_id, actor, FaceCommand.model_validate(row.command), runtime(row)
        )
    assert result.state == "queued"


@pytest.mark.asyncio
async def test_changed_intent_under_existing_job_id_never_creates_another_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, initial = job_rows()
    dispatch = AsyncMock()
    monkeypatch.setattr(job_service, "dispatch_one", dispatch)
    async with AsyncSession() as session:
        prepare(monkeypatch, session, row, initial)
        monkeypatch.setattr(session, "scalar", AsyncMock(return_value=row))
        command = FaceCommand.model_validate(row.command).model_copy(
            update={"portrait_id": uuid4()}
        )
        with pytest.raises(ConflictError):
            await job_service.enqueue(
                session,
                row.workspace_id,
                WorkflowActor(actor_ref=row.actor_ref, kind="human"),
                command,
                runtime(row),
            )
    dispatch.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["cancel", "retry", "stale", "running", "config"])
async def test_state_updates_use_expected_sequence_and_explicit_recovery(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    row, initial = job_rows("failed", 1)
    active = runtime(row)
    if mode == "running":
        initial.state, initial.lease_until = "running", datetime.now(UTC) + timedelta(seconds=120)
    if mode == "config":
        row.config_id = "c" * 64
    update = JobUpdate(
        job_id=row.id,
        request_id=uuid4(),
        expected_sequence=1 if mode == "stale" else 0,
        action="cancel" if mode == "cancel" else "retry",
    )
    monkeypatch.setattr(job_service, "dispatch_one", AsyncMock(return_value=False))
    async with AsyncSession() as session:
        events, _mocks = prepare(monkeypatch, session, row, initial)
        monkeypatch.setattr(session, "scalar", AsyncMock(return_value=None))
        actor = WorkflowActor(actor_ref=row.actor_ref, kind="human")
        if mode in {"stale", "running", "config"}:
            with pytest.raises(ConflictError):
                await job_service.update(session, row.workspace_id, actor, update, active)
            assert len(events) == 1
        else:
            result = await job_service.update(session, row.workspace_id, actor, update, active)
            assert result.state == ("cancelled" if mode == "cancel" else "queued")
            assert result.attempts == 1 and result.sequence == 1
            if mode == "retry":
                assert events[-1].dispatch_id != initial.dispatch_id


@pytest.mark.asyncio
async def test_dispatch_denial_precedes_task_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    row, initial = job_rows()
    active = runtime(row)
    async with AsyncSession() as session:
        _events, mocks = prepare(monkeypatch, session, row, initial)
        mocks["job_service.owned"].side_effect = AccessDeniedError("removed")
        assert not await job_service.dispatch_one(session, row.workspace_id, row.id, active)
    assert isinstance(active.dispatcher, AsyncMock)
    active.dispatcher.dispatch.assert_not_called()


def test_recovery_is_time_and_attempt_bounded_and_does_not_change_receipt_identity() -> None:
    row, event = job_rows()
    assert not recoverable(event, datetime.now(UTC))
    assert recoverable(event, event.recorded_at + timedelta(minutes=2))
    event.attempts = 3
    assert not recoverable(event, event.recorded_at + timedelta(days=1))
    event.attempts = 0
    assert receipt(row, event).job_id == row.request_id
    event.sequence = 29
    assert not recoverable(event, event.recorded_at + timedelta(days=1))
