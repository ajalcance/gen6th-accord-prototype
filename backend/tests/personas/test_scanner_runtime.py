"""Mock OS process boundary only: no native executable or definition is run."""

import asyncio
import os
import platform
import pwd
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from accord.scanner import filesystem, launcher, runtime
from personas.scanner_fixtures import SyntheticChild


@pytest.fixture
def native(monkeypatch: pytest.MonkeyPatch) -> runtime.ScannerRuntime:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(os, "geteuid", lambda: 100)
    monkeypatch.setattr(pwd, "getpwnam", lambda _: SimpleNamespace(pw_uid=100))
    monkeypatch.setattr(filesystem, "validate_seeds", Mock())
    monkeypatch.setattr(filesystem, "configuration", Mock())
    monkeypatch.setattr(filesystem, "updated_inventory", Mock())
    monkeypatch.setattr(filesystem, "database_snapshot", Mock(return_value={"daily.cvd": "digest"}))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock())
    return runtime.ScannerRuntime()


def install_processes(monkeypatch: pytest.MonkeyPatch) -> tuple[list[str], list[SyntheticChild]]:
    commands: list[str] = []
    handles: list[SyntheticChild] = []

    async def spawn(*args: str, **kwargs: object) -> SyntheticChild:
        commands.append(args[0])
        assert kwargs == {
            "stdin": -3,
            "stdout": -3,
            "stderr": -3,
            "cwd": "/var/lib/accord-scanner",
            "env": launcher.ENVIRONMENT,
        }
        child = SyntheticChild("clamd")
        if args[0] == "/usr/bin/freshclam" and "--daemon" in args:
            child.name = "freshclam"
        if args[0] != "/usr/sbin/clamd" and "--daemon" not in args:
            child.exit(0)
        handles.append(child)
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    return commands, handles


async def test_real_runtime_order_and_no_restart(
    native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands, handles = install_processes(monkeypatch)
    assert not native.children
    with pytest.raises(RuntimeError, match="not prepared"):
        await native.start()
    await native.prepare()
    assert commands == ["/usr/bin/sigtool"] * 3 + ["/usr/bin/freshclam", "/usr/bin/clamscan"]
    assert not native.children and all(h.returncode == 0 for h in handles)
    await native.start()
    assert [child.name for child in native.children] == ["clamd", "freshclam"]
    with pytest.raises(RuntimeError, match="not prepared"):
        await native.start()
    with pytest.raises(RuntimeError, match="cannot restart"):
        await native.prepare()
    for child in native.children:
        child.terminate()


@pytest.mark.parametrize(
    "fault", ["seeds", "configuration", "inventory", "signature", "bootstrap", "load", "spawn"]
)
async def test_validation_failures_never_launch_long_lived_children(
    fault: str, native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands, _ = install_processes(monkeypatch)
    if fault in ("seeds", "configuration", "inventory"):
        target = {
            "seeds": "validate_seeds",
            "configuration": "configuration",
            "inventory": "database_snapshot",
        }[fault]
        monkeypatch.setattr(filesystem, target, Mock(side_effect=ValueError("private")))
    else:
        original = native.helper

        async def fail(command: launcher.Command) -> None:
            target = {"signature": "daily", "bootstrap": "bootstrap", "load": "load"}.get(fault)
            if command == target or fault == "spawn":
                raise RuntimeError("private")
            await original(command)

        monkeypatch.setattr(native, "helper", fail)
    with pytest.raises(RuntimeError, match="^scanner preparation unavailable$"):
        await native.prepare()
    assert not native.prepared and not native.children
    assert "/usr/sbin/clamd" not in commands


@pytest.mark.parametrize("mode", ["failure", "timeout", "cancel"])
async def test_helper_failure_timeout_and_cancel_reap(
    mode: str, native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = SyntheticChild("clamd")
    monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock(return_value=child))
    monkeypatch.setattr(runtime, "HELPER_SECONDS", 0.01)
    if mode == "failure":
        child.exit(2)
        with pytest.raises(RuntimeError, match="command failed"):
            await native.helper("load")
    elif mode == "timeout":
        with pytest.raises(TimeoutError):
            await native.helper("load")
    else:
        task = asyncio.create_task(native.helper("load"))
        while not native.launcher.handles:
            await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert child.returncode is not None


async def test_cancelled_spawn_that_completes_later_is_owned_and_reaped(
    native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate, entered = asyncio.Event(), asyncio.Event()
    child = SyntheticChild("clamd")

    async def delayed(*args: str, **kwargs: object) -> SyntheticChild:
        entered.set()
        await gate.wait()
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", delayed)
    monkeypatch.setattr(launcher, "ACQUIRE_SECONDS", 0.01)
    task = asyncio.create_task(native.launcher.spawn("clamd"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert native.launcher.pending and native.launcher.failed
    with pytest.raises(RuntimeError, match="launcher unavailable"):
        await native.launcher.spawn("freshclam")
    gate.set()
    pending = tuple(native.launcher.pending)
    await asyncio.gather(*pending)
    assert child.returncode == 0 and child.signals == ["TERM"]
    assert native.children[0].returncode == 0


async def test_partial_start_is_registered_before_second_spawn(
    native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_processes(monkeypatch)
    await native.prepare()
    original = native.launcher.spawn

    async def fail(command: launcher.Command) -> launcher.NativeHandle:
        if command == "freshclam":
            assert len(native.children) == 1
            raise RuntimeError("second spawn failed")
        return await original(command)

    monkeypatch.setattr(native.launcher, "spawn", fail)
    with pytest.raises(RuntimeError, match="second spawn"):
        await native.start()
    assert len(native.children) == 1
    native.children[0].terminate()


@pytest.mark.parametrize("fault", ["platform", "architecture", "root", "account"])
def test_platform_denials(
    fault: str, native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    if fault == "platform":
        monkeypatch.setattr(sys, "platform", "darwin")
    if fault == "architecture":
        monkeypatch.setattr(platform, "machine", lambda: "arm64")
    if fault == "root":
        monkeypatch.setattr(os, "geteuid", lambda: 0)
    if fault == "account":
        monkeypatch.setattr(pwd, "getpwnam", lambda _: SimpleNamespace(pw_uid=101))
    with pytest.raises(ValueError, match="platform unavailable"):
        runtime.ScannerRuntime()


@pytest.mark.parametrize("when", ["load", "start"])
async def test_changed_loaded_bytes_deny(
    when: str, native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_processes(monkeypatch)
    values = [{"daily.cvd": "first"}, {"daily.cvd": "second"}]
    if when == "load":
        monkeypatch.setattr(filesystem, "database_snapshot", Mock(side_effect=values))
        with pytest.raises(RuntimeError, match="preparation unavailable"):
            await native.prepare()
    else:
        await native.prepare()
        monkeypatch.setattr(filesystem, "database_snapshot", Mock(return_value=values[1]))
        with pytest.raises(RuntimeError, match="loaded database changed"):
            await native.start()
    assert not native.children


async def test_failed_os_acquisition_has_no_child(
    native: runtime.ScannerRuntime, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        asyncio, "create_subprocess_exec", AsyncMock(side_effect=OSError("private"))
    )
    with pytest.raises(OSError):
        await native.launcher.spawn("clamd")
    assert native.launcher.failed and not native.children and not native.launcher.pending


@pytest.mark.parametrize("fault", ["resist", "term", "kill", "lookup", "wait"])
async def test_native_helper_cleanup_faults(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    child = SyntheticChild("clamd", resist_term=True)
    handle = launcher.NativeHandle(Mock(wraps=child))
    # Mock(wraps=...) does not forward properties: keep a real protocol-compatible object.
    monkeypatch.setattr(handle, "process", child)
    monkeypatch.setattr(launcher, "TERM_SECONDS", 0.01)
    monkeypatch.setattr(launcher, "KILL_SECONDS", 0.01)
    if fault == "term":
        monkeypatch.setattr(child, "terminate", Mock(side_effect=RuntimeError("private")))
    if fault == "kill":
        monkeypatch.setattr(child, "kill", Mock(side_effect=RuntimeError("private")))
    if fault == "lookup":
        monkeypatch.setattr(child, "terminate", Mock(side_effect=ProcessLookupError()))
    if fault == "wait":
        monkeypatch.setattr(child, "wait", AsyncMock(side_effect=RuntimeError("private")))
    if fault in ("resist", "lookup"):
        await handle.close()
        assert child.returncode == -9
    else:
        with pytest.raises((RuntimeError, TimeoutError)):
            await handle.close()


async def test_cancellation_during_owned_helper_cleanup_is_shielded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    child = SyntheticChild("clamd", resist_term=True)
    handle = launcher.NativeHandle(Mock())
    monkeypatch.setattr(handle, "process", child)
    monkeypatch.setattr(launcher, "TERM_SECONDS", 0.02)
    task = asyncio.create_task(launcher.protected_close(handle))
    while not child.signals:
        await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert child.returncode == -9
