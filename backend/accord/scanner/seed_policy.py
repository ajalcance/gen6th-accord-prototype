"""Build-only configuration emitter; requires actual pinned native verifier and CVD files.

No downloads, synthetic inputs, ownership changes or executable selection. This is not a
release acceptance record. Final assembly must supply reviewed inputs at the fixed paths.
"""

import asyncio
import hashlib
import json
import os
import platform
import re
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from accord.scanner import filesystem, launcher, policy

SIGTOOL = Path("/usr/bin/sigtool")
VERIFIER_LIMIT = 16 * 1024 * 1024
VERIFICATION_SECONDS = 30


def digest_value(value: str) -> str:
    if not re.fullmatch("[0-9a-f]{64}", value) or len(set(value)) == 1:
        raise ValueError("scanner input digest unavailable")
    return value


def seed_snapshot() -> dict[str, str]:
    for path in (policy.DATABASE, policy.TEMPORARY):
        info = filesystem.secure_path(path, policy.UID, directory=True)
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("scanner seed directory permissions unavailable")
    if any(policy.TEMPORARY.iterdir()):
        raise ValueError("scanner temporary store not fresh")
    if {path.name for path in policy.DATABASE.iterdir()} != set(policy.SEEDS):
        raise ValueError("scanner initial seed inventory unavailable")
    return {name: filesystem.seed_digest(policy.DATABASE / name) for name in policy.SEEDS}


def verifier_digest() -> str:
    info = filesystem.secure_path(SIGTOOL, 0)
    if not info.st_mode & stat.S_IXUSR:
        raise ValueError("scanner verifier unavailable")
    return hashlib.sha256(filesystem.read_file(SIGTOOL, 0, VERIFIER_LIMIT)).hexdigest()


async def verify_signature(command: launcher.Command) -> None:
    process_launcher = launcher.Launcher()
    handle = await process_launcher.spawn(command)
    try:
        if await asyncio.wait_for(handle.wait(), VERIFICATION_SECONDS) != 0:
            raise RuntimeError("scanner seed signature unavailable")
    finally:
        await launcher.protected_close(handle)


async def verify_inputs(expected: Mapping[str, str], verifier_sha256: str) -> dict[str, str]:
    if set(expected) != set(policy.SEEDS):
        raise ValueError("scanner required seed digests unavailable")
    bound = {name: digest_value(expected[name]) for name in policy.SEEDS}
    verifier = digest_value(verifier_sha256)
    if verifier_digest() != verifier or seed_snapshot() != bound:
        raise ValueError("scanner pinned input mismatch")
    for name in policy.SEEDS:
        await verify_signature(cast(launcher.Command, name.removesuffix(".cvd")))
    if verifier_digest() != verifier or seed_snapshot() != bound:
        raise ValueError("scanner verified input changed")
    return bound


def write_exclusive(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


async def emit_configuration(expected: Mapping[str, str], verifier_sha256: str) -> None:
    if sys.platform != "linux" or platform.machine() != "x86_64" or os.geteuid() != 0:
        raise ValueError("scanner assembly platform unavailable")
    filesystem.secure_path(policy.CONFIG, 0, directory=True)
    if any(policy.CONFIG.iterdir()):
        raise ValueError("scanner configuration destination not fresh")
    bound = await verify_inputs(expected, verifier_sha256)
    for name, content in policy.CONFIGURATIONS.items():
        write_exclusive(policy.CONFIG / name, content)
    # Last output is the existing runtime's exact manifest, never a placeholder template.
    write_exclusive(
        policy.CONFIG / "seeds.json", (json.dumps(bound, sort_keys=True) + "\n").encode()
    )
    filesystem.validate_seeds()
