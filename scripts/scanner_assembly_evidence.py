"""Strict scanner assembly binding. Call only after signature verification; no live probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

import release_evidence
import scanner_image_binding as binding
import scanner_launch_guard as launch

LIMIT = 20 * 1024 * 1024
REPORTS = {
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
}
CHECKS = {
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
}
CONTEXT = {"tag", "commit", "run_url", "image"}
FORBIDDEN = {"tests", "fixtures", "testdata", "node_modules", ".cache", ".git", ".env"}


def object_fields(value: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("missing, extra or invalid fields")
    return value


def text(value: Any, pattern: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("invalid evidence value")
    return value


def positive(value: Any) -> None:
    if type(value) not in (int, float) or not 0 < value < float("inf"):
        raise ValueError("missing measured peak")


def read(path: Path, limit: int = LIMIT) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing or indirect artifact")
    return binding.read(path, limit)


def decode(data: bytes) -> Any:
    return json.loads(data, object_pairs_hook=launch.unique_object)


def context(document: dict[str, Any], expected: dict[str, Any]) -> None:
    if any(document.get(key) != expected[key] for key in CONTEXT):
        raise ValueError("artifact context mismatch")


def release(path: Path, tag: str) -> dict[str, Any]:
    document = object_fields(
        decode(read(path)),
        {
            "schema_version",
            "tag",
            "commit",
            "run_url",
            "built_at",
            "components",
            "production_readiness",
        },
    )
    if release_evidence.validate(path, tag, quiet=True, require_clean=True):
        raise ValueError("release not accepted")
    if type(document["schema_version"]) is not int:
        raise ValueError("invalid schema type")
    text(
        document["run_url"],
        r"https://github.com/ajalcance/gen6th-accord/actions/runs/[1-9][0-9]*",
    )
    return document


def artifacts(document: dict[str, Any], directory: Path) -> dict[str, bytes]:
    records = object_fields(document["reports"], REPORTS)
    result: dict[str, bytes] = {}
    names: set[str] = set()
    for role, entry in records.items():
        entry = object_fields(entry, {"file", "sha256"})
        name = text(entry["file"], r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
        if name in names:
            raise ValueError("duplicate report filename")
        names.add(name)
        wanted = text(entry["sha256"], r"[0-9a-f]{64}")
        data = read(directory / name)
        if hashlib.sha256(data).hexdigest() != wanted:
            raise ValueError("artifact bytes changed")
        result[role] = data
    return result


def report(data: bytes, fields: set[str], expected: dict[str, Any]) -> dict[str, Any]:
    document = object_fields(decode(data), CONTEXT | fields)
    context(document, expected)
    return document


def native(data: bytes, expected: dict[str, Any]) -> None:
    document = report(data, {"platform", "checks", "peaks"}, expected)
    if document["platform"] != "linux/amd64":
        raise ValueError("native platform mismatch")
    checks = object_fields(document["checks"], CHECKS)
    if any(value != "passed" for value in checks.values()):
        raise ValueError("native acceptance incomplete")
    peaks = object_fields(document["peaks"], {"memory_bytes", "cpu_cores", "writable_bytes"})
    for value in peaks.values():
        positive(value)


def layer_bytes(path: Path, descriptor: dict[str, Any]) -> list[str]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != descriptor["size"]:
        raise ValueError("missing or changed layer bytes")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if "sha256:" + digest.hexdigest() != descriptor["digest"]:
        raise ValueError("layer bytes do not match manifest")
    names: list[str] = []
    with tarfile.open(path, mode="r|*") as archive:
        for entry in archive:
            if len(names) >= 100000:
                raise ValueError("layer inventory too large")
            names.append(entry.name)
            if entry.issym() or entry.islnk():
                if ".." in Path(entry.linkname).parts:
                    raise ValueError("unsafe runtime link")
    return names


def layers(data: bytes, manifest: bytes, expected: dict[str, Any], directory: Path) -> None:
    document = report(data, {"layers"}, expected)
    descriptors = decode(manifest)["layers"]
    inventory = document["layers"]
    if not isinstance(inventory, list) or len(inventory) != len(descriptors):
        raise ValueError("uninspected image layers")
    for record, descriptor in zip(inventory, descriptors, strict=True):
        record = object_fields(record, {"digest", "files", "blob_file"})
        if record["digest"] != descriptor["digest"]:
            raise ValueError("layer mismatch")
        files = record["files"]
        if not isinstance(files, list) or not files:
            raise ValueError("empty layer inventory")
        if len(files) != len(set(files)):
            raise ValueError("duplicate layer path")
        blob = text(record["blob_file"], r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
        if files != layer_bytes(directory / blob, descriptor):
            raise ValueError("reported paths differ from actual layer inventory")
        for name in files:
            name = text(name, r"[^\x00-\x1f\x7f]{1,4096}")
            parts = Path(name).parts
            if (
                Path(name).is_absolute()
                or ".." in parts
                or FORBIDDEN & {part.lower() for part in parts}
            ):
                raise ValueError("fixture, cache or secret path in layer")
            if any(word in name.lower() for word in ("mock_provider", "test-only")):
                raise ValueError("forbidden runtime material")


def inputs(data: bytes, expected: dict[str, Any]) -> None:
    document = report(data, {"hashes", "source_key_fingerprint", "signature_verified"}, expected)
    hashes = object_fields(
        document["hashes"],
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
    )
    for value in hashes.values():
        text(value, r"[0-9a-f]{64}")
        if len(set(value)) == 1:
            raise ValueError("placeholder input hash")
    text(document["source_key_fingerprint"], r"[0-9A-F]{40}")
    if document["signature_verified"] is not True:
        raise ValueError("source signature not verified")


def additional(data: dict[str, bytes], expected: dict[str, Any]) -> None:
    seeds = report(data["seeds"], {"cvds", "verified_at", "signature_verified"}, expected)
    cvds = object_fields(seeds["cvds"], {"main.cvd", "daily.cvd", "bytecode.cvd"})
    for value in cvds.values():
        text(value, r"[0-9a-f]{64}")
    datetime.strptime(seeds["verified_at"], "%Y-%m-%dT%H:%M:%SZ")
    if seeds["signature_verified"] is not True:
        raise ValueError("unverified seeds")
    configs = report(data["configs"], {"files"}, expected)
    values = object_fields(configs["files"], {"clamd.conf", "freshclam.conf", "seeds.json"})
    for value in values.values():
        text(value, r"[0-9a-f]{64}")
    scan = report(data["scan"], {"passed", "policy"}, expected)
    if scan["passed"] is not True or scan["policy"] != {
        "severity": "high",
        "only_fixed": True,
    }:
        raise ValueError("scanner scan not accepted")
    if scan["policy"]["only_fixed"] is not True:
        raise ValueError("scan policy type mismatch")
    scan_findings(data["scan_raw"])
    notices = report(data["notices"], {"license_review", "corresponding_source"}, expected)
    if notices["license_review"] != "passed" or notices["corresponding_source"] != "retained":
        raise ValueError("license obligations incomplete")


def scan_findings(data: bytes) -> None:
    raw_scan = decode(data)
    if not isinstance(raw_scan, dict) or not isinstance(raw_scan.get("matches"), list):
        raise ValueError("scan output missing")
    for match in raw_scan["matches"]:
        if not isinstance(match, dict) or not isinstance(match.get("vulnerability"), dict):
            raise ValueError("invalid scan finding")
        vulnerability = match["vulnerability"]
        severity = text(vulnerability.get("severity"), r"[A-Za-z]+")
        if severity.lower() in {"high", "critical"}:
            fix = vulnerability.get("fix")
            if not isinstance(fix, dict) or not isinstance(fix.get("state"), str):
                raise ValueError("missing vulnerability fix state")
            if fix["state"] == "fixed":
                raise ValueError("fixable high vulnerability")


def validate(path: Path, release_path: Path, directory: Path, tag: str) -> dict[str, Any]:
    document = object_fields(
        decode(read(path)),
        {
            "schema_version",
            "tag",
            "commit",
            "run_url",
            "image",
            "platform",
            "reports",
        },
    )
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValueError("assembly schema mismatch")
    if document["platform"] != "linux/amd64":
        raise ValueError("assembly platform mismatch")
    evidence = release(release_path, tag)
    if document["tag"] != tag:
        raise ValueError("assembly tag mismatch")
    text(document["image"], launch.IMAGE.pattern)
    context(document, {**evidence, "image": document["image"]})
    components = [item for item in evidence["components"] if item["name"] == "scanner"]
    if len(components) != 1 or components[0]["image"] != document["image"]:
        raise ValueError("mandatory scanner component mismatch")
    data = artifacts(document, directory)
    if components[0]["sbom_file"] != document["reports"]["sbom"]["file"]:
        raise ValueError("scanner SBOM filename mismatch")
    if components[0]["sbom_sha256"] != document["reports"]["sbom"]["sha256"]:
        raise ValueError("scanner SBOM digest mismatch")
    config = binding.bind(data["manifest"], data["image_config"], document["image"])
    launch.validate(config, decode(data["service"]), document["image"])
    inputs(data["inputs"], document)
    native(data["native"], document)
    layers(data["layers"], data["manifest"], document, directory)
    additional(data, document)
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    try:
        validate(args.assembly, args.release, args.artifacts, args.tag)
    except (OSError, ValueError, TypeError, KeyError, OverflowError, tarfile.TarError):
        print("scanner-assembly: FAILED — incomplete or mismatched evidence")
        return 1
    print("scanner-assembly: OK — bound reports; signatures/native execution checked separately")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
