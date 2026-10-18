"""Synthetic monotonic progress, recovery, cancellation and deadline evidence."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from accord.command import compliance_supervisor as module
from accord.command.compliance_supervisor import ComplianceSupervisor


async def test_empty_pass_progress_failure_recovery_and_staleness() -> None:
    now = [100.0]
    run = AsyncMock(return_value=(0, 0, 0))
    worker = ComplianceSupervisor(run, 2, lambda: now[0])
    assert worker.health() == "starting"
    await worker.cycle()
    assert worker.health() == "progressing"
    now[0] += module.PASS_SECONDS + 8
    assert worker.health() == "stalled"
    run.side_effect = RuntimeError("synthetic private failure")
    with pytest.raises(RuntimeError):
        await worker.cycle()
    assert worker.health() == "failed" and worker.last_success == 100
    run.side_effect = None
    await worker.cycle()
    assert worker.health() == "progressing"
    await worker.stop()
    assert worker.health() == "stopping"


@pytest.mark.parametrize("suppress_cancel", [False, True])
async def test_pass_deadline_never_counts_as_progress(
    monkeypatch: pytest.MonkeyPatch, suppress_cancel: bool
) -> None:
    monkeypatch.setattr(module, "PASS_SECONDS", 0.01)

    async def blocked() -> tuple[int, int, int]:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if not suppress_cancel:
                raise
        return (0, 0, 0)

    worker = ComplianceSupervisor(blocked, 2)
    with pytest.raises(TimeoutError):
        await worker.cycle()
    assert worker.health() == "failed" and worker.last_success is None


async def test_stop_cancels_pass_and_runs_its_cleanup_before_return() -> None:
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def blocked() -> tuple[int, int, int]:
        try:
            entered.set()
            await asyncio.Event().wait()
        finally:
            cleaned.set()
        return (0, 0, 0)

    worker = ComplianceSupervisor(blocked, 0.001)
    worker.start()
    await asyncio.wait_for(entered.wait(), 1)
    await worker.stop()
    assert cleaned.is_set() and worker.last_success is None
    assert worker.task is not None and worker.task.cancelled()
    assert worker.health() == "stopping"


async def test_stop_timeout_is_not_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "CANCEL_SECONDS", 0.01)
    entered, release = asyncio.Event(), asyncio.Event()

    async def resistant() -> tuple[int, int, int]:
        entered.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            await release.wait()
        return (0, 0, 0)

    worker = ComplianceSupervisor(resistant, 0.001)
    worker.start()
    await asyncio.wait_for(entered.wait(), 1)
    try:
        with pytest.raises(RuntimeError, match="cancellation deadline exceeded"):
            await worker.stop()
        assert worker.health() == "stopping" and worker.last_success is None
    finally:
        release.set()
        assert worker.task is not None
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(worker.task, 1)
    assert worker.last_success is None


async def test_loop_recovers_without_exposing_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    recovered = asyncio.Event()
    calls = 0

    async def run() -> tuple[int, int, int]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("synthetic-private-detail")
        recovered.set()
        return (0, 0, 0)

    worker = ComplianceSupervisor(run, 0.001)
    worker.start()
    await asyncio.wait_for(recovered.wait(), 1)
    assert worker.health() == "progressing"
    await worker.stop()
    assert "synthetic-private-detail" not in caplog.text
    assert "compliance pass unavailable" in caplog.text


async def test_finished_runner_and_restart_never_report_health() -> None:
    worker = ComplianceSupervisor(AsyncMock(return_value=(0, 0, 0)), 2)
    await worker.cycle()
    worker.start()
    with pytest.raises(RuntimeError):
        worker.start()
    assert worker.task is not None
    worker.task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await worker.task
    assert worker.health() == "failed"
    await worker.stop()
    with pytest.raises(RuntimeError):
        worker.start()
