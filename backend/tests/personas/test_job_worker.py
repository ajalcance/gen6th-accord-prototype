"""Stored actor/configuration, duplicate delivery, lease expiry and bounded failure proofs."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import job_worker
from accord.personas.repository import AccessDeniedError
from accord.personas.task_google import TaskReference
from personas.job_test_support import face_result, prepare, runtime
from personas.runtime_fixtures import job_rows


@pytest.mark.asyncio
async def test_worker_uses_stored_actor_and_duplicate_delivery_reuses_completed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, initial = job_rows()
    process = AsyncMock(return_value=face_result(row))
    monkeypatch.setattr(job_worker, "process_in_transaction", process)
    ref = TaskReference(
        workspace_id=row.workspace_id, job_id=row.id, dispatch_id=initial.dispatch_id
    )
    async with AsyncSession() as session:
        events, _mocks = prepare(monkeypatch, session, row, initial)
        await job_worker.execute(session, ref, runtime(row), "verified-workload")
        await job_worker.execute(session, ref, runtime(row), "verified-workload")
    assert [e.state for e in events] == ["queued", "running", "succeeded"]
    assert (
        events[-1].attempts == 1 and events[-1].generation_id == process.return_value.generation_id
    )
    process.assert_awaited_once()
    assert process.call_args.args[2] == row.actor_ref


@pytest.mark.asyncio
async def test_provider_failures_retain_attempts_and_stop_at_three(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, initial = job_rows()
    process = AsyncMock(side_effect=RuntimeError("sensitive-provider-error"))
    monkeypatch.setattr(job_worker, "process_in_transaction", process)
    ref = TaskReference(
        workspace_id=row.workspace_id, job_id=row.id, dispatch_id=initial.dispatch_id
    )
    async with AsyncSession() as session:
        events, _mocks = prepare(monkeypatch, session, row, initial)
        for _attempt in range(3):
            with pytest.raises(RuntimeError, match="job processing unavailable"):
                await job_worker.execute(session, ref, runtime(row), "verified-workload")
        await job_worker.execute(session, ref, runtime(row), "verified-workload")
    assert process.await_count == 3 and events[-1].state == "failed" and events[-1].attempts == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["scope", "dispatch", "configuration", "membership", "lease"])
async def test_no_provider_call_before_task_binding_and_fresh_authorization(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    row, initial = job_rows()
    process = AsyncMock()
    monkeypatch.setattr(job_worker, "process_in_transaction", process)
    ref = TaskReference(
        workspace_id=uuid4() if mode == "scope" else row.workspace_id,
        job_id=row.id,
        dispatch_id=uuid4() if mode == "dispatch" else initial.dispatch_id,
    )
    active = runtime(row)
    async with AsyncSession() as session:
        events, mocks = prepare(monkeypatch, session, row, initial)
        if mode == "configuration":
            row.config_id = "c" * 64
        if mode == "membership":
            mocks["job_worker.owned"].side_effect = AccessDeniedError("removed")
        if mode == "lease":
            initial.state = "running"
            initial.lease_until = datetime.now(UTC) + timedelta(seconds=120)
        if mode in {"scope", "lease"}:
            with pytest.raises((AccessDeniedError, RuntimeError)):
                await job_worker.execute(session, ref, active, "verified-workload")
        else:
            await job_worker.execute(session, ref, active, "verified-workload")
        assert events[-1].state == (
            "cancelled" if mode in {"configuration", "membership"} else initial.state
        )
    process.assert_not_called()


@pytest.mark.asyncio
async def test_abandoned_lease_can_recover_but_never_restarts_an_active_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, initial = job_rows("running", 1)
    initial.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    process = AsyncMock(return_value=face_result(row))
    monkeypatch.setattr(job_worker, "process_in_transaction", process)
    ref = TaskReference(
        workspace_id=row.workspace_id, job_id=row.id, dispatch_id=initial.dispatch_id
    )
    async with AsyncSession() as session:
        events, _mocks = prepare(monkeypatch, session, row, initial)
        await job_worker.execute(session, ref, runtime(row), "verified-workload")
    assert events[-1].state == "succeeded" and events[-1].attempts == 2
    process.assert_awaited_once()
