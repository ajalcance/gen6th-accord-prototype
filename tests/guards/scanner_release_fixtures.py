"""Generated artifact bytes for scanner guard fault tests only; never runtime inputs."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

from conftest import SCRIPTS, load_module


def module(monkeypatch: Any, name: str) -> Any:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return load_module(SCRIPTS / name)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value))


def update(path: Path, **changes: Any) -> None:
    value = json.loads(path.read_text())
    value.update(changes)
    write_json(path, value)


def image_manifest(directory: Path, guard: Any, config_bytes: bytes, name: str) -> bytes:
    layer_path = directory / "scanner-layer.tar"
    with tarfile.open(layer_path, "w") as archive:
        content = b"generated test content"
        member = tarfile.TarInfo(name)
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))
    layer_bytes = layer_path.read_bytes()
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": guard.binding.digest(config_bytes),
            "size": len(config_bytes),
        },
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar",
                "digest": guard.binding.digest(layer_bytes),
                "size": len(layer_bytes),
            }
        ],
    }
    return json.dumps(manifest).encode()


def package(
    directory: Path,
    monkeypatch: Any,
    name: str = "usr/bin/clamd",
) -> tuple[Any, Path, Path]:
    guard = module(monkeypatch, "scanner_assembly_evidence.py")
    launch_tests = load_module(Path(__file__).with_name("test_scanner_launch_guard.py"))
    config, service = launch_tests.documents()
    config_bytes = json.dumps(config).encode()
    manifest_bytes = image_manifest(directory, guard, config_bytes, name)
    manifest = json.loads(manifest_bytes)
    image = "ghcr.io/ajalcance/gen6th-accord-scanner@" + guard.binding.digest(manifest_bytes)
    service["spec"]["template"]["spec"]["containers"][1]["image"] = image
    context = {
        "tag": "v1.2.3",
        "commit": "ab" * 20,
        "image": image,
        "run_url": "https://github.com/ajalcance/gen6th-accord/actions/runs/123",
    }
    payloads = report_payloads(guard, context, manifest)
    layers = json.loads(payloads["layers"])
    layers["layers"][0]["files"] = [name]
    payloads["layers"] = json.dumps(layers).encode()
    payloads.update(
        {
            "manifest": manifest_bytes,
            "image_config": config_bytes,
            "service": json.dumps(service).encode(),
            "sbom": b'{"spdxVersion":"SPDX-2.3"}',
        }
    )
    records = save_reports(directory, payloads)
    assembly, release = save_evidence(directory, context, records)
    return guard, assembly, release


def save_reports(directory: Path, payloads: dict[str, bytes]) -> dict[str, Any]:
    records = {}
    for role, data in payloads.items():
        name = "sbom-scanner.spdx.json" if role == "sbom" else f"scanner-{role}.json"
        (directory / name).write_bytes(data)
        records[role] = {"file": name, "sha256": hashlib.sha256(data).hexdigest()}
    return records


def save_evidence(
    directory: Path,
    context: dict[str, str],
    records: dict[str, Any],
) -> tuple[Path, Path]:
    evidence = {
        "schema_version": 1,
        **{key: context[key] for key in ("tag", "commit", "run_url")},
        "built_at": "2026-10-12T00:00:00Z",
        "production_readiness": {
            "clean": True,
            "open_blockers": [],
        },
        "components": [
            {
                "name": "scanner",
                "image": context["image"],
                "sbom_file": records["sbom"]["file"],
                "sbom_sha256": records["sbom"]["sha256"],
            }
        ],
    }
    release = directory / "release-evidence.json"
    assembly = directory / "scanner-assembly.json"
    write_json(release, evidence)
    write_json(
        assembly,
        {
            "schema_version": 1,
            **context,
            "platform": "linux/amd64",
            "reports": records,
        },
    )
    return assembly, release


def report_payloads(guard: Any, context: dict[str, str], manifest: Any) -> dict[str, bytes]:
    values = {
        "native": {
            "platform": "linux/amd64",
            "checks": dict.fromkeys(guard.CHECKS, "passed"),
            "peaks": {"memory_bytes": 100, "cpu_cores": 1.2, "writable_bytes": 100},
        },
        "inputs": input_receipt(),
        "layers": {
            "layers": [
                {
                    "digest": manifest["layers"][0]["digest"],
                    "files": ["usr/bin/clamd"],
                    "blob_file": "scanner-layer.tar",
                }
            ]
        },
        "scan": {"passed": True, "policy": {"severity": "high", "only_fixed": True}},
        "seeds": {
            "cvds": dict.fromkeys(("main.cvd", "daily.cvd", "bytecode.cvd"), "ab" * 32),
            "signature_verified": True,
            "verified_at": "2026-10-12T00:00:00Z",
        },
        "configs": {
            "files": dict.fromkeys(("clamd.conf", "freshclam.conf", "seeds.json"), "ab" * 32)
        },
        "notices": {"license_review": "passed", "corresponding_source": "retained"},
    }
    encoded = {role: json.dumps({**context, **value}).encode() for role, value in values.items()}
    encoded["scan_raw"] = b'{"matches":[]}'
    return encoded


def input_receipt() -> dict[str, Any]:
    return {
        "hashes": dict.fromkeys(
            {
                "base_manifest",
                "builder_manifest",
                "source_archive",
                "source_signature",
                "native_snapshot",
                "native_lock",
                "cargo_lock",
                "cargo_vendor",
                "python_lock",
                "compile_options",
            },
            "ab" * 32,
        ),
        "source_key_fingerprint": "AB" * 20,
        "signature_verified": True,
    }


def rebind_report(assembly: Path, role: str) -> None:
    document = json.loads(assembly.read_text())
    entry = document["reports"][role]
    entry["sha256"] = hashlib.sha256((assembly.parent / entry["file"]).read_bytes()).hexdigest()
    write_json(assembly, document)
