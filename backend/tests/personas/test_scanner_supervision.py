"""Synthetic preparation/order, fixed probe, freshness, failure and cancellation."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_scanner import ScanReceipt
from accord.scanner import processes
from accord.scanner import supervisor as module
from accord.scanner.processes import shutdown_children
from accord.scanner.supervisor import ScannerSupervisor
from personas.scanner_fixtures import SyntheticRuntime

RECEIPT = ScanReceipt("ClamAV 1.4.3", "12345")


async def test_prepare_then_start_probe_staleness_failure_recovery() -> None:
    runtime, now = SyntheticRuntime(), [100.0]
    probe = AsyncMock(return_value=RECEIPT)
    runner = ScannerSupervisor(runtime, probe, lambda: now[0])
    assert runner.health() == "starting"
    await runner.initialize()
    assert runtime.prepared and runner.health() == "ready"
    now[0] += module.SUCCESS_AGE_SECONDS + 1
    assert runner.health() == "stalled"
    probe.side_effect = PhotoUnavailableError("synthetic stale receipt")
    assert not await runner.check() and runner.health() == "unavailable"
    probe.side_effect = None
    assert await runner.check() and runner.health() == "ready"
    runtime.updater.exit(0)
    assert runner.health() == "failed"
    with pytest.raises(RuntimeError, match="children unavailable"):
        await runner.check()
    await shutdown_children(runtime.children)


@pytest.mark.parametrize("stage", ["prepare", "partial", "probe"])
async def test_stop_during_startup_cleans_every_registered_child(
    stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "POLL_SECONDS", 0.001)
    runtime, probing = SyntheticRuntime(), asyncio.Event()
    if stage == "prepare":
        runtime.prepare_gate = asyncio.Event()
    if stage == "partial":
        runtime.partial_gate = asyncio.Event()

    async def blocked_probe() -> ScanReceipt:
        probing.set()
        await asyncio.Event().wait()
        return RECEIPT

    runner = ScannerSupervisor(runtime, blocked_probe)
    runner.start()
    await asyncio.wait_for(runtime.entered.wait(), 1)
    if stage == "partial":
        while not runtime.children:
            await asyncio.sleep(0)
    if stage == "probe":
        await asyncio.wait_for(probing.wait(), 1)
    await runner.stop()
    assert runner.health() == "stopping" and runner.last_success is None
    assert all(child.returncode is not None for child in runtime.children)
    with pytest.raises(RuntimeError, match="cannot restart"):
        runner.start()


@pytest.mark.parametrize("failure", ["validation", "blocked", "probe"])
async def test_startup_failure_never_ready_and_reaps_children(
    failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "STARTUP_SECONDS", 0.02)
    monkeypatch.setattr(module, "POLL_SECONDS", 0.001)
    runtime = SyntheticRuntime()
    runtime.prepare_failure = failure == "validation"
    if failure == "blocked":
        runtime.prepare_gate = asyncio.Event()
    probe = AsyncMock(side_effect=PhotoUnavailableError("synthetic private detail"))
    runner = ScannerSupervisor(runtime, probe)
    runner.start()
    assert runner.task is not None
    await asyncio.wait_for(runner.task, 1)
    assert runner.health() == "failed" and runner.last_success is None
    assert all(child.returncode is not None for child in runtime.children)
    if failure != "probe":
        probe.assert_not_called()
    await runner.stop()


@pytest.mark.parametrize("child", ["daemon", "updater"])
async def test_child_death_denies_health_and_stops_peer(
    child: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "POLL_SECONDS", 0.001)
    runtime, ready = SyntheticRuntime(), asyncio.Event()

    async def probe() -> ScanReceipt:
        ready.set()
        return RECEIPT

    runner = ScannerSupervisor(runtime, probe)
    runner.start()
    await asyncio.wait_for(ready.wait(), 1)
    assert runner.health() == "ready"
    getattr(runtime, child).exit(0)  # Even an unexpected successful exit is fatal.
    assert runner.health() == "failed"
    assert runner.task is not None
    await asyncio.wait_for(runner.task, 1)
    assert all(c.returncode is not None for c in runtime.children)
    await runner.stop()


@pytest.mark.parametrize("suppress", [False, True])
async def test_expired_probe_never_refreshes_success(
    suppress: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "PROBE_SECONDS", 0.01)
    runtime = SyntheticRuntime()

    async def blocked() -> ScanReceipt:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if not suppress:
                raise
        return RECEIPT

    runner = ScannerSupervisor(runtime, blocked)
    await runtime.prepare()
    await runtime.start()
    assert not await runner.check() and runner.last_success is None
    await shutdown_children(runtime.children)


@pytest.mark.parametrize("fault", ["stale", "malformed", "pong"])
async def test_default_probe_reuses_existing_fixed_freshness_guard(
    fault: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = SyntheticRuntime()
    runner = ScannerSupervisor(runtime)
    await runtime.prepare()
    await runtime.start()
    date = (datetime.now(UTC) - timedelta(hours=49)).strftime("%a %b %d %H:%M:%S %Y")
    version = f"ClamAV 1.4.3/12345/{date}".encode() + bytes([0])
    replies = [b"PONG" + bytes([0]), version]
    if fault == "malformed":
        replies[1] = b"unavailable" + bytes([0])
    if fault == "pong":
        replies[0] = b"unavailable" + bytes([0])
    command = AsyncMock(side_effect=replies)
    monkeypatch.setattr("accord.personas.scanner_probe.ClamdScanner.command", command)
    assert not await runner.check() and runner.last_success is None
    commands = [call.args[0] for call in command.await_args_list]
    assert commands == (
        [b"zPING" + bytes([0])]
        if fault == "pong"
        else [b"zPING" + bytes([0]), b"zVERSION" + bytes([0])]
    )
    await shutdown_children(runtime.children)


async def test_stop_timeout_is_not_clean_acknowledgment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "STOP_SECONDS", 0.01)
    runtime, release = SyntheticRuntime(), asyncio.Event()

    async def resistant_prepare() -> None:
        runtime.entered.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            await release.wait()

    monkeypatch.setattr(runtime, "prepare", resistant_prepare)
    runner = ScannerSupervisor(runtime, AsyncMock(return_value=RECEIPT))
    runner.start()
    await asyncio.wait_for(runtime.entered.wait(), 1)
    try:
        with pytest.raises(RuntimeError, match="stop deadline exceeded"):
            await runner.stop()
        assert runner.health() == "stopping" and runner.last_success is None
    finally:
        release.set()
        assert runner.task is not None
        await asyncio.wait_for(runner.task, 1)


async def test_stop_during_failure_cleanup_does_not_abort_reaping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "POLL_SECONDS", 0.001)
    monkeypatch.setattr(processes, "TERM_SECONDS", 0.02)
    runtime, ready, term = SyntheticRuntime(), asyncio.Event(), asyncio.Event()
    runtime.daemon.resist_term = True
    original = runtime.daemon.terminate

    def terminate() -> None:
        original()
        term.set()

    async def probe() -> ScanReceipt:
        ready.set()
        return RECEIPT

    monkeypatch.setattr(runtime.daemon, "terminate", terminate)
    runner = ScannerSupervisor(runtime, probe)
    runner.start()
    await asyncio.wait_for(ready.wait(), 1)
    runtime.updater.exit(1)
    await asyncio.wait_for(term.wait(), 1)
    await runner.stop()
    await runner.stop()
    assert runtime.daemon.signals == ["TERM", "KILL"]
    assert all(child.returncode is not None for child in runtime.children)


async def test_cleanup_exception_is_generic_and_denies_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = SyntheticRuntime()
    runner = ScannerSupervisor(runtime, AsyncMock(return_value=RECEIPT))
    runtime.prepare_failure = True

    async def failed_cleanup() -> None:
        raise RuntimeError("synthetic private child error")

    monkeypatch.setattr(runner, "cleanup", failed_cleanup)
    runner.start()
    assert runner.task is not None
    with pytest.raises(RuntimeError, match="^scanner supervision cleanup unavailable$"):
        await runner.task
    assert runner.health() == "failed"
    with pytest.raises(RuntimeError, match="^scanner supervision stop unavailable$"):
        await runner.stop()


async def test_duplicate_start_prestarted_runtime_and_immediate_stop_denied() -> None:
    runtime = SyntheticRuntime()
    runner = ScannerSupervisor(runtime, AsyncMock(return_value=RECEIPT))
    runner.start()
    with pytest.raises(RuntimeError, match="cannot restart"):
        runner.start()
    await runner.stop()
    assert not runtime.prepared and runner.health() == "stopping"
    await runtime.prepare()
    await runtime.start()
    with pytest.raises(ValueError, match="already started"):
        ScannerSupervisor(runtime)
    await shutdown_children(runtime.children)
