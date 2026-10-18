"""scanner_release_gate.py and scanner_assembly_emit.py boundaries use test-only tool spies."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import SCRIPTS, run_guard
from scanner_release_fixtures import module, package


@pytest.mark.parametrize("mode", ["candidate", "promote", "destination"])
def test_each_boundary_verifies_images_and_destination(
    tmp_path: Path,
    monkeypatch: Any,
    mode: str,
) -> None:
    _, assembly, release = package(tmp_path, monkeypatch)
    gate = module(monkeypatch, "scanner_release_gate.py")
    calls: list[list[str]] = []
    image = json.loads(assembly.read_text())["image"]
    for path in (assembly, release):
        path.with_suffix(".bundle").write_text("generated test bundle")
    destination = "asia-southeast1-docker.pkg.dev/example/images/scanner@" + image.split("@")[1]

    def command(args: list[str]) -> str:
        calls.append(args)
        return image.split("@")[1] if args[0] == "crane" else ""

    monkeypatch.setattr(gate, "command", command)
    gate.gate(
        assembly,
        release,
        tmp_path,
        "v1.2.3",
        mode,
        destination if mode == "destination" else None,
    )
    verifies = [args for args in calls if args[0] == "cosign"]
    assert verifies
    for args in verifies:
        assert args[args.index("--certificate-identity") + 1] == (
            "https://github.com/ajalcance/gen6th-accord/.github/workflows/release.yml@refs/tags/v1.2.3"
        )
        assert args[args.index("--certificate-oidc-issuer") + 1] == (
            "https://token.actions.githubusercontent.com"
        )
    assert sum(args[1] == "verify-blob" for args in verifies) == (0 if mode == "candidate" else 2)
    assert all(
        args[:2] in (["cosign", "verify"], ["cosign", "verify-blob"], ["crane", "digest"])
        for args in calls
    )
    if mode == "destination":
        assert calls[-2:] == [
            ["crane", "digest", image],
            ["crane", "digest", destination],
        ]


@pytest.mark.parametrize(
    "stage",
    [
        "release-signature",
        "assembly-signature",
        "image-signature",
        "source-digest",
        "destination-digest",
    ],
)
def test_failures_stop_before_any_mutation(
    tmp_path: Path,
    monkeypatch: Any,
    stage: str,
) -> None:
    _, assembly, release = package(tmp_path, monkeypatch)
    gate = module(monkeypatch, "scanner_release_gate.py")
    image = json.loads(assembly.read_text())["image"]
    destination = "asia-southeast1-docker.pkg.dev/example/images/scanner@" + image.split("@")[1]
    for path in (assembly, release):
        path.with_suffix(".bundle").write_text("generated test bundle")
    calls: list[list[str]] = []

    def command(args: list[str]) -> str:
        calls.append(args)
        if stage == "release-signature" and args[-1] == str(release):
            raise subprocess.CalledProcessError(1, args)
        if stage == "assembly-signature" and args[-1] == str(assembly):
            raise subprocess.CalledProcessError(1, args)
        if stage == "image-signature" and args[:2] == ["cosign", "verify"]:
            raise subprocess.CalledProcessError(1, args)
        if args[0] == "crane":
            if (stage == "source-digest" and args[-1] == image) or (
                stage == "destination-digest" and args[-1] == destination
            ):
                return "sha256:" + "cd" * 32
            return image.split("@")[1]
        return ""

    monkeypatch.setattr(gate, "command", command)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        gate.gate(assembly, release, tmp_path, "v1.2.3", "destination", destination)
    assert all(args[1] in ("verify", "verify-blob", "digest") for args in calls)


def test_signature_rejection_precedes_raw_artifact_validation(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _, assembly, release = package(tmp_path, monkeypatch)
    gate = module(monkeypatch, "scanner_release_gate.py")
    release.with_suffix(".bundle").write_text("generated test bundle")
    (tmp_path / "scanner-manifest.json").unlink()

    def reject(args: list[str]) -> str:
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(gate, "command", reject)
    with pytest.raises(subprocess.CalledProcessError):
        gate.gate(assembly, release, tmp_path, "v1.2.3", "promote", None)


def test_missing_signature_cli_denies_without_tools(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _, assembly, release = package(tmp_path, monkeypatch)
    result = run_guard(
        SCRIPTS / "scanner_release_gate.py",
        "--mode",
        "promote",
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
    assert result.stdout == "scanner-release: FAILED — unverifiable scanner release boundary\n"


def test_emitter_binds_existing_reports_without_overwrite(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    guard, _, release = package(tmp_path, monkeypatch)
    emitter = module(monkeypatch, "scanner_assembly_emit.py")
    out = tmp_path / "emitted.json"
    emitter.emit(tmp_path, release, out, "v1.2.3")
    guard.validate(out, release, tmp_path, "v1.2.3")
    before = out.read_bytes()
    with pytest.raises(ValueError):
        emitter.emit(tmp_path, release, out, "v1.2.3")
    assert out.read_bytes() == before


def test_emitter_missing_reports_leaves_no_consumable_document(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _, _, release = package(tmp_path, monkeypatch)
    emitter = module(monkeypatch, "scanner_assembly_emit.py")
    (tmp_path / "scanner-native.json").unlink()
    out = tmp_path / "emitted.json"
    with pytest.raises((OSError, ValueError)):
        emitter.emit(tmp_path, release, out, "v1.2.3")
    assert not out.exists()
