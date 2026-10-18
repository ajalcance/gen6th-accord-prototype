"""Mandatory scanner publication/promotion/destination gate; never copies or deploys images."""

from __future__ import annotations

import argparse
import re
import subprocess
import tarfile
from pathlib import Path
from typing import Any

import release_evidence
import scanner_assembly_evidence as assembly
import scanner_launch_guard as launch

REPOSITORY = "ajalcance/gen6th-accord"
ISSUER = "https://token.actions.githubusercontent.com"


def command(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=True, timeout=120)
    return result.stdout.strip()


def identity(tag: str) -> str:
    if not release_evidence.TAG_RE.fullmatch(tag):
        raise ValueError("invalid tag")
    return f"https://github.com/{REPOSITORY}/.github/workflows/release.yml@refs/tags/{tag}"


def verify_blob(path: Path, tag: str) -> None:
    assembly.read(path)
    bundle = path.with_suffix(".bundle")
    assembly.read(bundle)
    command(
        [
            "cosign",
            "verify-blob",
            "--bundle",
            str(bundle),
            "--certificate-identity",
            identity(tag),
            "--certificate-oidc-issuer",
            ISSUER,
            str(path),
        ]
    )


def verify_image(image: str, tag: str) -> None:
    assembly.text(image, launch.IMAGE.pattern)
    command(
        [
            "cosign",
            "verify",
            image,
            "--certificate-identity",
            identity(tag),
            "--certificate-oidc-issuer",
            ISSUER,
        ]
    )


def gate(
    assembly_path: Path,
    release_path: Path,
    directory: Path,
    tag: str,
    mode: str,
    destination: str | None,
) -> dict[str, Any]:
    if mode not in {"candidate", "promote", "destination"}:
        raise ValueError("unknown boundary")
    if mode != "candidate":
        verify_blob(release_path, tag)
        verify_blob(assembly_path, tag)
    for component in assembly.release(release_path, tag)["components"]:
        verify_image(component["image"], tag)
    document = assembly.validate(assembly_path, release_path, directory, tag)
    if mode == "destination":
        if destination is None:
            raise ValueError("destination required")
        assembly.text(destination, r"[a-z0-9-]+-docker\.pkg\.dev/[a-z0-9._/-]+@sha256:[0-9a-f]{64}")
        verify_image(destination, tag)
        expected = document["image"].split("@")[1]
        if destination.split("@")[1] != expected:
            raise ValueError("destination reference mismatch")
        for image in (document["image"], destination):
            digest = command(["crane", "digest", image])
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest) or digest != expected:
                raise ValueError("registry manifest changed")
    elif destination is not None:
        raise ValueError("unexpected destination")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("candidate", "promote", "destination"), required=True)
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--destination")
    args = parser.parse_args()
    try:
        gate(
            args.assembly,
            args.release,
            args.artifacts,
            args.tag,
            args.mode,
            args.destination,
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ):
        print("scanner-release: FAILED — unverifiable scanner release boundary")
        return 1
    print("scanner-release: OK — signatures, assembly and required scanner checked; no deployment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
