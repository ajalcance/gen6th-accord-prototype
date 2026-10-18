"""Candidate ADR-0071 structural guard; not wired into active CI or release acceptance.

Consumes an actual OCI image configuration and Knative v1 service JSON. The future
release/import pipeline must bind those input bytes to the verified image and reviewed
deployment. This validator does not perform signatures, image acquisition or deployment.
"""

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

COMMAND = [
    "uvicorn",
    "accord.scanner.production:create_app",
    "--factory",
    "--host",
    "0.0.0.0",
    "--port",
    "8091",
    "--workers",
    "1",
    "--no-access-log",
    "--no-proxy-headers",
    "--no-server-header",
    "--lifespan",
    "on",
    "--timeout-graceful-shutdown",
    "2",
]
IMAGE = re.compile(r"[a-z0-9.-]+(?::[0-9]+)?/[a-z0-9._/-]+@sha256:[0-9a-f]{64}")
DEPENDENCIES = "run.googleapis.com/container-dependencies"
LIMIT = 256 * 1024


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def load(path: Path) -> Any:
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("input exceeds bound")
    return json.loads(data, object_pairs_hook=unique_object)


def object_value(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(label + " must be an object")
    return value


def image_configuration(image: Any) -> None:
    document = object_value(image, "OCI configuration")
    if document.get("os") != "linux" or document.get("architecture") != "amd64":
        raise ValueError("scanner platform mismatch")
    config = object_value(document.get("config"), "OCI runtime configuration")
    if config.get("User") != "100" or config.get("Cmd") != COMMAND:
        raise ValueError("scanner UID or command mismatch")
    if config.get("Entrypoint") not in (None, []):
        raise ValueError("scanner entrypoint override")
    env = config.get("Env")
    if not isinstance(env, list) or any(not isinstance(item, str) for item in env):
        raise ValueError("scanner environment unavailable")
    names: set[str] = set()
    for item in env:
        name, separator, _ = item.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or name in names:
            raise ValueError("scanner environment ambiguous")
        names.add(name)
        if name.startswith("UVICORN_") or name in {
            "WEB_CONCURRENCY",
            "PYTHONPATH",
            "PYTHONHOME",
        }:
            raise ValueError("scanner environment override")


def health_probe(value: Any) -> None:
    probe = object_value(value, "scanner startup probe")
    if set(probe) - {
        "httpGet",
        "initialDelaySeconds",
        "timeoutSeconds",
        "periodSeconds",
        "failureThreshold",
    }:
        raise ValueError("scanner probe override")
    if probe.get("httpGet") != {"path": "/health", "port": 8091}:
        raise ValueError("scanner native HTTP probe mismatch")
    delay = probe.get("initialDelaySeconds", 0)
    if type(delay) is not int or delay != 0:
        raise ValueError("scanner probe delay")
    for key in ("timeoutSeconds", "periodSeconds", "failureThreshold"):
        if type(probe.get(key)) is not int or probe[key] <= 0:
            raise ValueError("scanner probe bounds unavailable")
    if probe["timeoutSeconds"] > probe["periodSeconds"]:
        raise ValueError("scanner probe timeout exceeds period")
    # This guard checks bounds only; no specific timing/allocation is selected here.
    if probe["failureThreshold"] * probe["periodSeconds"] > 600:
        raise ValueError("scanner probe exceeds platform startup bound")


def topology(service: Any, scanner_image: str) -> None:
    if not IMAGE.fullmatch(scanner_image):
        raise ValueError("scanner reference is not immutable")
    if len(set(scanner_image.rsplit(":", 1)[1])) == 1:
        raise ValueError("scanner placeholder digest")
    document = object_value(service, "service")
    if document.get("apiVersion") != "serving.knative.dev/v1" or document.get("kind") != "Service":
        raise ValueError("expected Knative v1 service")
    spec = object_value(document.get("spec"), "service spec")
    template = object_value(spec.get("template"), "service template")
    instance = object_value(template.get("spec"), "instance spec")
    containers = instance.get("containers")
    if not isinstance(containers, list) or len(containers) != 3:
        raise ValueError("expected three reviewed containers")
    named: dict[str, Mapping[str, Any]] = {}
    for item in containers:
        container = object_value(item, "container")
        name = container.get("name")
        if (
            not isinstance(name, str)
            or name not in {"api", "scanner", "sql-proxy"}
            or name in named
        ):
            raise ValueError("container names unavailable or duplicated")
        named[name] = container
    if named["api"].get("ports") != [{"containerPort": 8000}]:
        raise ValueError("API ingress mismatch")
    for name in ("scanner", "sql-proxy"):
        if "ports" in named[name]:
            raise ValueError("sidecar must not claim ingress")
    scanner = named["scanner"]
    if scanner.get("image") != scanner_image:
        raise ValueError("scanner deployment digest mismatch")
    if set(scanner) - {"name", "image", "resources", "startupProbe"}:
        raise ValueError("scanner deployment override")
    health_probe(scanner.get("startupProbe"))
    metadata = object_value(template.get("metadata"), "template metadata")
    annotations = object_value(metadata.get("annotations"), "template annotations")
    encoded = annotations.get(DEPENDENCIES)
    if not isinstance(encoded, str):
        raise ValueError("startup dependencies unavailable")
    dependencies = json.loads(encoded, object_pairs_hook=unique_object)
    if dependencies != {"api": ["scanner", "sql-proxy"]}:
        raise ValueError("API startup dependencies mismatch")


def validate(image: Any, service: Any, scanner_image: str) -> None:
    image_configuration(image)
    topology(service, scanner_image)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-config", type=Path, required=True)
    parser.add_argument("--service", type=Path, required=True)
    parser.add_argument("--scanner-image", required=True)
    args = parser.parse_args()
    try:
        validate(load(args.image_config), load(args.service), args.scanner_image)
    except (OSError, ValueError, TypeError, KeyError):
        print("scanner-launch: FAILED — unverified launch or topology inputs")
        return 1
    print("scanner-launch: checked one OCI configuration and one service; structural match only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
