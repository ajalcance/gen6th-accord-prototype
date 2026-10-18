"""Temporary filesystem policy evidence; seed bytes exist exclusively in this test module."""

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from accord.scanner import filesystem, policy


@pytest.fixture
def layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config, database, temporary = (tmp_path / name for name in ("config", "database", "temporary"))
    for path in (config, database, temporary):
        path.mkdir(mode=0o700)
    monkeypatch.setattr(policy, "CONFIG", config)
    monkeypatch.setattr(policy, "DATABASE", database)
    monkeypatch.setattr(policy, "TEMPORARY", temporary)
    monkeypatch.setattr(policy, "EXECUTABLES", ())
    monkeypatch.setattr(filesystem, "secure_path", lambda path, uid, **kwargs: path.lstat())
    for name, content in policy.CONFIGURATIONS.items():
        (config / name).write_bytes(content)
    seeds: dict[str, str] = {}
    for name in policy.SEEDS:
        content = (name.encode() * 100)[:600]
        (database / name).write_bytes(content)
        seeds[name] = hashlib.sha256(content).hexdigest()
    (config / "seeds.json").write_text(json.dumps(seeds))
    return tmp_path


def test_exact_seed_validation_and_updated_inventory(layout: Path) -> None:
    filesystem.validate_seeds()
    (policy.DATABASE / "daily.cvd").rename(policy.DATABASE / "daily.cld")
    (policy.DATABASE / "freshclam.dat").write_bytes(b"updater-state")
    filesystem.updated_inventory()
    with pytest.raises(ValueError, match="not fresh"):
        filesystem.validate_seeds()


@pytest.mark.parametrize(
    "fault",
    [
        "unknown",
        "duplicate",
        "override",
        "missing",
        "extra",
        "digest",
        "small",
        "large",
        "temporary",
    ],
)
def test_bad_configuration_seed_and_inventory_denied(
    fault: str, layout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if fault in ("unknown", "duplicate", "override"):
        value = {
            "unknown": b"OnUpdateExecute command\n",
            "duplicate": b"MaxThreads 2\n",
            "override": b"TCPAddr 0.0.0.0\n",
        }[fault]
        (policy.CONFIG / "clamd.conf").write_bytes(policy.CLAMD + value)
    if fault == "missing":
        (policy.DATABASE / "daily.cvd").unlink()
    if fault == "extra":
        (policy.DATABASE / "local.ndb").write_bytes(b"local")
    if fault == "digest":
        (policy.DATABASE / "daily.cvd").write_bytes(b"changed" * 100)
    if fault == "small":
        (policy.DATABASE / "daily.cvd").write_bytes(b"small")
    if fault == "large":
        monkeypatch.setattr(policy, "MAX_DATABASE_BYTES", 512)
    if fault == "temporary":
        (policy.TEMPORARY / "leftover").write_bytes(b"data")
    with pytest.raises(ValueError):
        filesystem.validate_seeds()


@pytest.mark.parametrize("value", ["{}", '{"main.cvd":"x","main.cvd":"y"}', "[]", "null"])
def test_invalid_manifest_denied(value: str, layout: Path) -> None:
    (policy.CONFIG / "seeds.json").write_text(value)
    with pytest.raises(ValueError):
        filesystem.seed_inventory()


@pytest.mark.parametrize("value", ["0" * 64, "z" * 64, 12, {"nested": "object"}])
def test_invalid_or_placeholder_digest_denied(value: object, layout: Path) -> None:
    (policy.CONFIG / "seeds.json").write_text(json.dumps(dict.fromkeys(policy.SEEDS, value)))
    with pytest.raises(ValueError):
        filesystem.seed_inventory()


@pytest.mark.parametrize("fault", ["extra", "both", "empty", "missing"])
def test_updated_inventory_denials(fault: str, layout: Path) -> None:
    if fault == "extra":
        (policy.DATABASE / "custom.ldb").write_bytes(b"data")
    if fault == "both":
        (policy.DATABASE / "daily.cld").write_bytes(b"data")
    if fault == "empty":
        (policy.DATABASE / "main.cvd").write_bytes(b"")
    if fault == "missing":
        (policy.DATABASE / "main.cvd").unlink()
    with pytest.raises(ValueError):
        filesystem.updated_inventory()


@pytest.mark.parametrize(
    "fault",
    ["symlink", "owner", "writable", "hardlink", "setuid", "parent", "directory", "owned_parent"],
)
def test_no_follow_ownership_and_permissions(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    path = Path("/controlled/file")
    mode, uid, links = stat.S_IFREG | 0o600, 100, 1
    if fault == "symlink":
        mode = stat.S_IFLNK | 0o777
    if fault == "owner":
        uid = 101
    if fault == "writable":
        mode |= 0o020
    if fault == "hardlink":
        links = 2
    if fault == "setuid":
        mode |= 0o4000
    if fault == "directory":
        mode = stat.S_IFDIR | 0o700

    def info(current: Path) -> os.stat_result:
        if current == path:
            return os.stat_result((mode, 1, 1, links, uid, 100, 600, 0, 0, 0))
        parent_mode = stat.S_IFDIR | (0o777 if fault == "parent" else 0o755)
        parent_uid = 100 if fault == "owned_parent" and current == path.parent else 0
        return os.stat_result((parent_mode, 1, 1, 1, parent_uid, 0, 0, 0, 0, 0))

    if fault == "owned_parent":
        monkeypatch.setattr(policy, "DATABASE", path.parent)
    monkeypatch.setattr(Path, "lstat", info)
    with pytest.raises(ValueError):
        filesystem.secure_path(path, 100)


def test_file_bound_and_descriptor_change(layout: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="exceeds bound"):
        filesystem.read_file(policy.CONFIG / "clamd.conf", 0, 1)
    original = os.fstat
    count = 0

    def changed(descriptor: int) -> os.stat_result:
        nonlocal count
        count += 1
        info = original(descriptor)
        if count > 1:
            fields = list(info)
            fields[6] += 1
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(os, "fstat", changed)
    with pytest.raises(ValueError, match="changed"):
        filesystem.read_file(policy.CONFIG / "clamd.conf", 0, 4096)


def test_configuration_extra_file(layout: Path) -> None:
    (policy.CONFIG / "unknown.conf").write_bytes(b"data")
    with pytest.raises(ValueError, match="inventory"):
        filesystem.configuration()


def test_database_snapshot_binds_loaded_bytes(layout: Path) -> None:
    before = filesystem.database_snapshot()
    (policy.DATABASE / "daily.cvd").write_bytes(b"changed" * 100)
    assert filesystem.database_snapshot() != before


@pytest.mark.parametrize("fault", ["executable", "permissions"])
def test_executable_and_directory_permissions_denied(
    fault: str, layout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if fault == "executable":
        file = layout / "executable"
        file.write_bytes(b"source-only fixture")
        file.chmod(0o600)
        monkeypatch.setattr(policy, "EXECUTABLES", (str(file),))
    else:
        policy.DATABASE.chmod(0o755)
    with pytest.raises(ValueError):
        filesystem.configuration()


@pytest.mark.parametrize("target", ["read", "seed"])
def test_descriptor_replacement_denied(
    target: str, layout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = os.fstat

    def different(descriptor: int) -> os.stat_result:
        fields = list(actual(descriptor))
        fields[1] += 1
        return os.stat_result(fields)

    monkeypatch.setattr(os, "fstat", different)
    with pytest.raises(ValueError, match="changed"):
        if target == "read":
            filesystem.read_file(policy.CONFIG / "clamd.conf", 0, 4096)
        else:
            filesystem.seed_digest(policy.DATABASE / "daily.cvd")
