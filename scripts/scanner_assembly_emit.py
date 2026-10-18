"""Emit scanner assembly from actual bounded reports; never manufactures acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

import scanner_assembly_evidence as assembly


def emit(directory: Path, release_path: Path, out: Path, tag: str) -> None:
    release = assembly.release(release_path, tag)
    scanners = [item for item in release["components"] if item["name"] == "scanner"]
    if len(scanners) != 1:
        raise ValueError("scanner required")
    reports = {}
    for role in sorted(assembly.REPORTS):
        name = scanners[0]["sbom_file"] if role == "sbom" else f"scanner-{role}.json"
        data = assembly.read(directory / name)
        reports[role] = {"file": name, "sha256": hashlib.sha256(data).hexdigest()}
    document = {
        "schema_version": 1,
        "tag": tag,
        "commit": release["commit"],
        "run_url": release["run_url"],
        "image": scanners[0]["image"],
        "platform": "linux/amd64",
        "reports": reports,
    }
    # Reject reports before writing a consumable assembly; validation uses a temporary file.
    temporary = out.with_suffix(".pending")
    if temporary.exists() or out.exists():
        raise ValueError("assembly output already exists")
    try:
        temporary.write_text(json.dumps(document, sort_keys=True) + "\n")
        assembly.validate(temporary, release_path, directory, tag)
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    try:
        emit(args.artifacts, args.release, args.out, args.tag)
    except (OSError, ValueError, TypeError, KeyError, tarfile.TarError):
        print("scanner-assembly-emit: FAILED — reports unavailable or rejected")
        return 1
    print("scanner-assembly-emit: OK — existing reports bound; not signed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
