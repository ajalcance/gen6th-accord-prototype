"""Fault tests of scanner_assembly_evidence.py, including actual CLI and actual layer archives."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import SCRIPTS, run_guard
from scanner_release_fixtures import package, rebind_report, update, write_json


def test_structural_acceptance_is_separate_from_signatures(
    tmp_path: Path, monkeypatch: Any
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    assert guard.validate(assembly, release, tmp_path, "v1.2.3")["platform"] == "linux/amd64"


@pytest.mark.parametrize(
    "role",
    [
        "inputs",
        "seeds",
        "configs",
        "layers",
        "native",
        "scan",
        "sbom",
        "manifest",
        "image_config",
        "service",
        "notices",
        "scan_raw",
    ],
)
@pytest.mark.parametrize("fault", ["missing", "changed", "symlink"])
def test_every_report_is_required_and_bound(
    tmp_path: Path,
    monkeypatch: Any,
    role: str,
    fault: str,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    document = json.loads(assembly.read_text())
    path = tmp_path / document["reports"][role]["file"]
    if fault == "missing":
        path.unlink()
    elif fault == "changed":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        target = tmp_path / "indirect.json"
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises(ValueError):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("tag", "v9.9.9"),
        ("commit", "cd" * 20),
        ("run_url", "https://github.com/other/repo/actions/runs/1"),
        ("platform", "linux/arm64"),
        ("image", "ghcr.io/example/scanner:latest"),
        ("unexpected", True),
        ("reports", []),
    ],
)
def test_assembly_context_and_shape(
    tmp_path: Path,
    monkeypatch: Any,
    key: str,
    value: Any,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    update(assembly, **{key: value})
    with pytest.raises(ValueError):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize("fault", ["missing", "wrong-image", "wrong-sbom", "open-blocker"])
def test_mandatory_component_and_release(
    tmp_path: Path,
    monkeypatch: Any,
    fault: str,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    document = json.loads(release.read_text())
    if fault == "missing":
        document["components"][0]["name"] = "backend"
    elif fault == "wrong-image":
        document["components"][0]["image"] = "ghcr.io/example/scanner@sha256:" + "cd" * 32
    elif fault == "wrong-sbom":
        document["components"][0]["sbom_sha256"] = "cd" * 32
    else:
        document["production_readiness"] = {"clean": False, "open_blockers": ["REAL-1"]}
    write_json(release, document)
    with pytest.raises(ValueError):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize(
    "check",
    [
        "import_closure",
        "layout",
        "engine_version",
        "seed_signature",
        "update",
        "load",
        "scan",
        "freshness_health",
        "term",
        "reaping",
        "restart",
        "private_probe",
    ],
)
def test_every_native_acceptance_case_must_pass(
    tmp_path: Path,
    monkeypatch: Any,
    check: str,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    path = tmp_path / "scanner-native.json"
    document = json.loads(path.read_text())
    document["checks"][check] = "blocked"
    write_json(path, document)
    rebind_report(assembly, "native")
    with pytest.raises(ValueError):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize("peak", ["memory_bytes", "cpu_cores", "writable_bytes"])
@pytest.mark.parametrize("value", [0, -1, True, "100", float("nan"), float("inf")])
def test_peaks_are_real_finite_measurements(
    tmp_path: Path,
    monkeypatch: Any,
    peak: str,
    value: Any,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    path = tmp_path / "scanner-native.json"
    document = json.loads(path.read_text())
    document["peaks"][peak] = value
    write_json(path, document)
    rebind_report(assembly, "native")
    with pytest.raises(ValueError):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize("fault", ["source", "seeds", "scan", "layer", "blob", "config", "license"])
def test_bound_but_unacceptable_reports(
    tmp_path: Path,
    monkeypatch: Any,
    fault: str,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch)
    role = {
        "source": "inputs",
        "seeds": "seeds",
        "scan": "scan",
        "layer": "layers",
        "blob": "layers",
        "config": "image_config",
        "license": "notices",
    }[fault]
    path = tmp_path / f"scanner-{role}.json"
    document = json.loads(path.read_text())
    if fault in ("source", "seeds"):
        document["signature_verified"] = False
    elif fault == "scan":
        document["passed"] = False
    elif fault == "layer":
        document["layers"][0]["files"] = ["tests/provider.py"]
    elif fault == "blob":
        (tmp_path / "scanner-layer.tar").write_bytes(b"changed")
    elif fault == "config":
        document["config"]["Cmd"].append("--reload")
    else:
        document["license_review"] = "pending"
    write_json(path, document)
    rebind_report(assembly, role)
    with pytest.raises(ValueError):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize(
    "encoded",
    [b"", b"{}", b'{"tag":1,"tag":2}', b"x" * (20 * 1024 * 1024 + 1)],
    ids=["empty", "missing-fields", "duplicate-key", "oversized"],
)
def test_cli_fails_closed_without_echo(
    tmp_path: Path,
    monkeypatch: Any,
    encoded: bytes,
) -> None:
    _, assembly, release = package(tmp_path, monkeypatch)
    assembly.write_bytes(encoded)
    result = run_guard(
        SCRIPTS / "scanner_assembly_evidence.py",
        "--assembly",
        str(assembly),
        "--release",
        str(release),
        "--artifacts",
        str(tmp_path),
        "--tag",
        "v1.2.3",
    )
    assert result.returncode == 1
    assert result.stderr == ""
    assert result.stdout == "scanner-assembly: FAILED — incomplete or mismatched evidence\n"


@pytest.mark.parametrize(
    "name",
    [
        "tests/provider.py",
        "usr/fixtures/record.json",
        "usr/mock_provider.py",
        "../../escape",
        "/absolute",
    ],
)
def test_actual_forbidden_layer_denied_with_matching_hashes(
    tmp_path: Path,
    monkeypatch: Any,
    name: str,
) -> None:
    guard, assembly, release = package(tmp_path, monkeypatch, name)
    with pytest.raises(ValueError, match="fixture|forbidden"):
        guard.validate(assembly, release, tmp_path, "v1.2.3")


@pytest.mark.parametrize(
    "matches",
    [
        None,
        [None],
        [{"vulnerability": {"severity": 1}}],
        [{"vulnerability": {"severity": "High"}}],
        [{"vulnerability": {"severity": "Critical", "fix": {"state": "fixed"}}}],
    ],
)
def test_raw_scan_faults_deny_at_cli_with_no_echo(
    tmp_path: Path,
    monkeypatch: Any,
    matches: Any,
) -> None:
    _, assembly, release = package(tmp_path, monkeypatch)
    write_json(tmp_path / "scanner-scan_raw.json", {"matches": matches})
    rebind_report(assembly, "scan_raw")
    result = run_guard(
        SCRIPTS / "scanner_assembly_evidence.py",
        "--assembly",
        str(assembly),
        "--release",
        str(release),
        "--artifacts",
        str(tmp_path),
        "--tag",
        "v1.2.3",
    )
    assert result.returncode == 1 and result.stderr == ""
    assert result.stdout == "scanner-assembly: FAILED — incomplete or mismatched evidence\n"
