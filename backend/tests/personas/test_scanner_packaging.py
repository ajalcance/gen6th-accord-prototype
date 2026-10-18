"""Isolated build-input tests; invented bytes and native process mocks never ship."""

import asyncio
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from accord.scanner import filesystem, launcher, policy, seed_policy
from personas.scanner_fixtures import SyntheticChild


@pytest.fixture
def inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, str], str]:
    for name, target in (("CONFIG", "config"), ("DATABASE", "data"), ("TEMPORARY", "temp")):
        path = tmp_path / target
        path.mkdir(mode=0o700)
        monkeypatch.setattr(policy, name, path)
    hashes: dict[str, str] = {}
    for name in policy.SEEDS:
        data = name.encode() * 100
        (policy.DATABASE / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    tool = tmp_path / "sigtool"
    tool.write_bytes(b"test-only verifier boundary")
    tool.chmod(0o700)
    monkeypatch.setattr(seed_policy, "SIGTOOL", tool)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(os, "geteuid", lambda: 0)

    def local_stat(path: Path, uid: int, *, directory: bool = False) -> os.stat_result:
        # Ownership enforcement has independent filesystem fault tests; preserve real IO here.
        return path.lstat()

    monkeypatch.setattr(filesystem, "secure_path", local_stat)
    monkeypatch.setattr(filesystem, "validate_seeds", Mock())
    child = SyntheticChild("clamd")
    child.exit(0)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", AsyncMock(return_value=child))
    return hashes, hashlib.sha256(tool.read_bytes()).hexdigest()


async def test_emitter_native_checks_precede_exact_manifest(
    inputs: tuple[dict[str, str], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[tuple[str, ...]] = []

    async def verify(*command: str, **options: object) -> SyntheticChild:
        assert not list(policy.CONFIG.iterdir())
        assert options == {
            "stdin": -3,
            "stdout": -3,
            "stderr": -3,
            "cwd": "/var/lib/accord-scanner",
            "env": launcher.ENVIRONMENT,
        }
        commands.append(command)
        child = SyntheticChild("clamd")
        child.exit(0)
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", verify)
    await seed_policy.emit_configuration(*inputs)
    assert commands == [launcher.COMMANDS[name] for name in ("main", "daily", "bytecode")]
    assert json.loads((policy.CONFIG / "seeds.json").read_bytes()) == inputs[0]
    assert {p.name for p in policy.CONFIG.iterdir()} == {*policy.CONFIGURATIONS, "seeds.json"}
    for name, content in policy.CONFIGURATIONS.items():
        assert (policy.CONFIG / name).read_bytes() == content
    with pytest.raises(ValueError, match="destination not fresh"):
        await seed_policy.emit_configuration(*inputs)


@pytest.mark.parametrize("value", ["", "a" * 64, "0" * 64, "f" * 63, "AB" * 32, "example"])
def test_digest_templates_denied(value: str) -> None:
    with pytest.raises(ValueError, match="digest unavailable"):
        seed_policy.digest_value(value)


@pytest.mark.parametrize("fault", ["missing", "extra", "cld", "empty-temp", "permissions"])
async def test_inventory_faults_deny_before_native_run(
    fault: str, inputs: tuple[dict[str, str], str]
) -> None:
    if fault == "missing":
        (policy.DATABASE / "daily.cvd").unlink()
    elif fault == "extra":
        (policy.DATABASE / "local.ndb").write_bytes(b"test only")
    elif fault == "cld":
        (policy.DATABASE / "daily.cvd").rename(policy.DATABASE / "daily.cld")
    elif fault == "empty-temp":
        (policy.TEMPORARY / "leftover").touch()
    else:
        policy.DATABASE.chmod(0o755)
    with pytest.raises(ValueError):
        await seed_policy.emit_configuration(*inputs)
    assert not list(policy.CONFIG.iterdir())
    assert isinstance(asyncio.create_subprocess_exec, AsyncMock)
    asyncio.create_subprocess_exec.assert_not_called()


@pytest.mark.parametrize("fault", ["seed", "verifier", "missing-key", "extra-key", "template"])
async def test_input_binding_denies(fault: str, inputs: tuple[dict[str, str], str]) -> None:
    expected, verifier = inputs
    if fault == "seed":
        (policy.DATABASE / "main.cvd").write_bytes(b"different test bytes" * 50)
    elif fault == "verifier":
        seed_policy.SIGTOOL.write_bytes(b"changed verifier")
    elif fault == "missing-key":
        expected.pop("main.cvd")
    elif fault == "extra-key":
        expected["daily.cld"] = expected["daily.cvd"]
    else:
        verifier = "0" * 64
    with pytest.raises(ValueError):
        await seed_policy.emit_configuration(expected, verifier)
    assert not list(policy.CONFIG.iterdir())
    assert isinstance(asyncio.create_subprocess_exec, AsyncMock)
    asyncio.create_subprocess_exec.assert_not_called()


@pytest.mark.parametrize("fault", ["seed", "verifier", "exit", "timeout", "unavailable"])
async def test_native_verification_or_changed_input_denies_output(
    fault: str, inputs: tuple[dict[str, str], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail(*args: object, **kwargs: object) -> SyntheticChild:
        if fault == "seed":
            (policy.DATABASE / "daily.cvd").write_bytes(b"changed during verification" * 50)
        elif fault == "verifier":
            seed_policy.SIGTOOL.write_bytes(b"changed during verification")
        elif fault == "exit":
            child = SyntheticChild("clamd")
            child.exit(1)
            return child
        elif fault == "timeout":
            raise TimeoutError
        else:
            raise FileNotFoundError
        child = SyntheticChild("clamd")
        child.exit(0)
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fail)
    with pytest.raises((ValueError, RuntimeError, OSError)):
        await seed_policy.emit_configuration(*inputs)
    assert not list(policy.CONFIG.iterdir())


@pytest.mark.parametrize("fault", ["platform", "architecture", "non-root", "not-executable"])
async def test_assembly_platform_denials(
    fault: str, inputs: tuple[dict[str, str], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    if fault == "platform":
        monkeypatch.setattr(sys, "platform", "darwin")
    elif fault == "architecture":
        monkeypatch.setattr(platform, "machine", lambda: "arm64")
    elif fault == "non-root":
        monkeypatch.setattr(os, "geteuid", lambda: 100)
    else:
        seed_policy.SIGTOOL.chmod(0o600)
    with pytest.raises(ValueError):
        await seed_policy.emit_configuration(*inputs)
    assert not list(policy.CONFIG.iterdir())


def test_exclusive_outputs_never_follow_or_replace(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.write_bytes(b"preserve")
    link = tmp_path / "link"
    link.symlink_to(target)
    for path in (target, link):
        with pytest.raises(FileExistsError):
            seed_policy.write_exclusive(path, b"replacement")
    assert target.read_bytes() == b"preserve"


@pytest.mark.parametrize("mode", ["cancel", "timeout"])
async def test_signature_wait_reaps_and_never_emits(
    mode: str, inputs: tuple[dict[str, str], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    child = SyntheticChild("clamd")
    entered = asyncio.Event()

    async def spawn(*args: str, **kwargs: object) -> SyntheticChild:
        entered.set()
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(seed_policy, "VERIFICATION_SECONDS", 0.01)
    task = asyncio.create_task(seed_policy.emit_configuration(*inputs))
    await entered.wait()
    if mode == "cancel":
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        with pytest.raises(TimeoutError):
            await task
    assert child.returncode == 0 and child.signals == ["TERM"]
    assert not list(policy.CONFIG.iterdir())


async def test_partial_output_is_not_resumable(
    inputs: tuple[dict[str, str], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = seed_policy.write_exclusive

    def interrupted(path: Path, content: bytes) -> None:
        if path.name == "bootstrap.conf":
            raise OSError("test interruption")
        original(path, content)

    monkeypatch.setattr(seed_policy, "write_exclusive", interrupted)
    with pytest.raises(OSError):
        await seed_policy.emit_configuration(*inputs)
    assert not (policy.CONFIG / "seeds.json").exists()
    with pytest.raises(ValueError, match="destination not fresh"):
        await seed_policy.emit_configuration(*inputs)
