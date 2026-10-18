"""Bounded no-follow file checks; root-owned policy anchors a fresh writable seed store."""

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from accord.scanner import policy


def secure_path(path: Path, uid: int, *, directory: bool = False) -> os.stat_result:
    for parent in reversed(path.parents):
        info = parent.lstat()
        owner = policy.UID if parent in (policy.DATABASE, policy.TEMPORARY) else 0
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != owner or info.st_mode & 0o022:
            raise ValueError("scanner parent unavailable")
        if owner != 0 and stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("scanner parent permissions unavailable")
    info = path.lstat()
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode) or info.st_uid != uid or info.st_mode & 0o6022:
        raise ValueError("scanner path unavailable")
    if not directory and info.st_nlink != 1:
        raise ValueError("scanner linked file unavailable")
    return info


def identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def read_file(path: Path, uid: int, limit: int) -> bytes:
    before = secure_path(path, uid)
    if before.st_size > limit:
        raise ValueError("scanner file exceeds bound")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if identity(opened) != identity(before):
            raise ValueError("scanner file changed")
        data = stream.read(limit + 1)
        if len(data) > limit or identity(os.fstat(stream.fileno())) != identity(opened):
            raise ValueError("scanner file changed")
    return data


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("scanner duplicate policy")
        result[key] = value
    return result


def configuration() -> None:
    secure_path(policy.CONFIG, 0, directory=True)
    if {p.name for p in policy.CONFIG.iterdir()} != {*policy.CONFIGURATIONS, "seeds.json"}:
        raise ValueError("scanner configuration inventory unavailable")
    for name, content in policy.CONFIGURATIONS.items():
        if read_file(policy.CONFIG / name, 0, 4096) != content:
            raise ValueError("scanner configuration mismatch")
    for executable in policy.EXECUTABLES:
        info = secure_path(Path(executable), 0)
        if not info.st_mode & stat.S_IXUSR:
            raise ValueError("scanner executable unavailable")
    for directory in (policy.DATABASE, policy.TEMPORARY):
        info = secure_path(directory, policy.UID, directory=True)
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("scanner writable permissions unavailable")
    if any(policy.TEMPORARY.iterdir()):
        raise ValueError("scanner temporary store not fresh")


def seed_inventory() -> dict[str, str]:
    content = read_file(policy.CONFIG / "seeds.json", 0, 1024)
    parsed: object = json.loads(content, object_pairs_hook=unique_object)
    if not isinstance(parsed, dict) or set(parsed) != set(policy.SEEDS):
        raise ValueError("scanner seed policy unavailable")
    result: dict[str, str] = {}
    for name in policy.SEEDS:
        value = parsed[name]
        if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
            raise ValueError("scanner seed digest unavailable")
        if len(set(value)) == 1:
            raise ValueError("scanner placeholder digest unavailable")
        result[name] = value
    return result


def seed_digest(path: Path) -> str:
    before = secure_path(path, policy.UID)
    if not 512 <= before.st_size <= policy.MAX_DATABASE_BYTES:
        raise ValueError("scanner seed size unavailable")
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if identity(opened) != identity(before):
            raise ValueError("scanner seed changed")
        total = 0
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > policy.MAX_DATABASE_BYTES:
                raise ValueError("scanner seed exceeds bound")
            digest.update(chunk)
        if identity(os.fstat(stream.fileno())) != identity(opened) or total != before.st_size:
            raise ValueError("scanner seed changed")
    return digest.hexdigest()


def validate_seeds() -> None:
    configuration()
    expected = seed_inventory()
    if {p.name for p in policy.DATABASE.iterdir()} != set(policy.SEEDS):
        raise ValueError("scanner seed store not fresh")
    for name, digest in expected.items():
        if seed_digest(policy.DATABASE / name) != digest:
            raise ValueError("scanner seed digest mismatch")


def updated_inventory() -> None:
    """Only the trusted updater may create incremental CLD and its state file."""
    names = {p.name for p in policy.DATABASE.iterdir()}
    required: set[str] = set()
    for seed in policy.SEEDS:
        choices = {seed, seed.removesuffix(".cvd") + ".cld"} & names
        if len(choices) != 1:
            raise ValueError("scanner updated database unavailable")
        required.update(choices)
    if names - required - {"freshclam.dat"}:
        raise ValueError("scanner unexpected updated database")
    for name in names:
        info = secure_path(policy.DATABASE / name, policy.UID)
        if not 0 < info.st_size <= policy.MAX_DATABASE_BYTES:
            raise ValueError("scanner updated database size unavailable")


def database_snapshot() -> dict[str, str]:
    updated_inventory()
    return {
        path.name: seed_digest(path)
        for path in policy.DATABASE.iterdir()
        if path.name != "freshclam.dat"
    }
