"""ADR-0070/0071 candidate: bind scanner launch inputs to exact image manifest bytes.

The calling release/import stage MUST first verify the expected image signature using
the existing reviewed identity/issuer policy. This check does not verify signatures,
fetch images, inspect layers or prove native acceptance. No active CI wiring yet.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import scanner_launch_guard as launch

DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
MANIFEST_TYPES = {
    "application/vnd.oci.image.manifest.v1+json": "application/vnd.oci.image.config.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json": (
        "application/vnd.docker.container.image.v1+json"
    ),
}
LAYER_TYPES = {
    "application/vnd.oci.image.layer.v1.tar",
    "application/vnd.oci.image.layer.v1.tar+gzip",
    "application/vnd.oci.image.layer.v1.tar+zstd",
    "application/vnd.docker.image.rootfs.diff.tar.gzip",
}
MANIFEST_LIMIT = 1024 * 1024


def read(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not data or len(data) > limit:
        raise ValueError("missing or oversized image input")
    return data


def decode(data: bytes) -> Any:
    return json.loads(data, object_pairs_hook=launch.unique_object)


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def descriptor(value: Any, media_types: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("invalid OCI descriptor")
    if value.get("mediaType") not in media_types:
        raise ValueError("unexpected OCI descriptor media type")
    if not isinstance(value.get("digest"), str) or not DIGEST.fullmatch(value["digest"]):
        raise ValueError("invalid OCI descriptor digest")
    if type(value.get("size")) is not int or value["size"] <= 0:
        raise ValueError("invalid OCI descriptor size")
    if "urls" in value or "data" in value:
        raise ValueError("external or embedded OCI descriptor")
    return value


def bind(manifest_bytes: bytes, config_bytes: bytes, scanner_image: str) -> Any:
    if not launch.IMAGE.fullmatch(scanner_image):
        raise ValueError("expected immutable scanner image")
    if not manifest_bytes or len(manifest_bytes) > MANIFEST_LIMIT:
        raise ValueError("missing or oversized manifest")
    if not config_bytes or len(config_bytes) > launch.LIMIT:
        raise ValueError("missing or oversized config")
    if scanner_image.rsplit("@", 1)[1] != digest(manifest_bytes):
        raise ValueError("manifest does not match expected image digest")
    manifest = launch.object_value(decode(manifest_bytes), "image manifest")
    if type(manifest.get("schemaVersion")) is not int or manifest["schemaVersion"] != 2:
        raise ValueError("unexpected manifest schema")
    media_type = manifest.get("mediaType")
    if not isinstance(media_type, str) or media_type not in MANIFEST_TYPES:
        raise ValueError("expected one image manifest, not an index or artifact")
    if {"manifests", "artifactType", "subject"} & set(manifest):
        raise ValueError("unexpected manifest topology")
    config = descriptor(manifest.get("config"), {MANIFEST_TYPES[media_type]})
    if config["digest"] != digest(config_bytes) or config["size"] != len(config_bytes):
        raise ValueError("configuration does not match image manifest")
    layers = manifest.get("layers")
    if not isinstance(layers, list) or not 1 <= len(layers) <= 128:
        raise ValueError("image layer population unavailable or oversized")
    for layer in layers:
        descriptor(layer, LAYER_TYPES)
    return decode(config_bytes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image-config", type=Path, required=True)
    parser.add_argument("--service", type=Path, required=True)
    parser.add_argument("--scanner-image", required=True)
    args = parser.parse_args()
    try:
        config = bind(
            read(args.manifest, MANIFEST_LIMIT),
            read(args.image_config, launch.LIMIT),
            args.scanner_image,
        )
        launch.validate(config, launch.load(args.service), args.scanner_image)
    except (OSError, ValueError, TypeError, KeyError):
        print("scanner-image-binding: FAILED — image or launch input mismatch")
        return 1
    print("scanner-image-binding: checked manifest/config digest chain and launch structure only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
