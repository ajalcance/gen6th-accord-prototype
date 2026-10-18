"""Fault tests for the isolated ADR-0071 candidate; all image/service data is test-only."""

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

GUARD = Path(__file__).with_name("scanner_launch_guard.py")
if not GUARD.is_file():
    GUARD = Path(__file__).resolve().parents[2] / "scripts/scanner_launch_guard.py"
SPEC = importlib.util.spec_from_file_location("scanner_launch_candidate", GUARD)
assert SPEC is not None and SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
IMAGE = "ghcr.io/example/test-only-scanner@sha256:" + "ab" * 32
EXPECTED_COMMAND = [
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


def documents() -> tuple[dict[str, Any], dict[str, Any]]:
    image = {
        "os": "linux",
        "architecture": "amd64",
        "config": {
            "User": "100",
            "Cmd": list(EXPECTED_COMMAND),
            "Env": ["PATH=/usr/bin"],
        },
    }
    scanner = {
        "name": "scanner",
        "image": IMAGE,
        "startupProbe": {
            "httpGet": {"path": "/health", "port": 8091},
            "initialDelaySeconds": 0,
            "timeoutSeconds": 2,
            "periodSeconds": 5,
            "failureThreshold": 30,
        },
    }
    service = {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        guard.DEPENDENCIES: json.dumps({"api": ["scanner", "sql-proxy"]})
                    }
                },
                "spec": {
                    "containers": [
                        {"name": "api", "ports": [{"containerPort": 8000}]},
                        scanner,
                        {"name": "sql-proxy"},
                    ]
                },
            },
        },
    }
    return image, service


def containers(service: dict[str, Any]) -> list[dict[str, Any]]:
    return service["spec"]["template"]["spec"]["containers"]


def test_reviewed_structure_passes() -> None:
    image, service = documents()
    guard.validate(image, service, IMAGE)


@pytest.mark.parametrize("index", range(len(EXPECTED_COMMAND)))
def test_every_command_element_is_fixed(index: int) -> None:
    image, service = documents()
    image["config"]["Cmd"][index] = "changed"
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize("extra", [["--reload"], ["--proxy-headers"], ["--access-log"]])
def test_extra_command_options_are_rejected(extra: list[str]) -> None:
    image, service = documents()
    image["config"]["Cmd"] += extra
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize(
    "key,value",
    [
        ("User", "0"),
        ("User", "100:100"),
        ("User", 100),
        ("Entrypoint", ["sh", "-c"]),
        ("Cmd", None),
        ("Env", None),
        ("Env", ["UVICORN_RELOAD=true"]),
        ("Env", ["UVICORN_HOST=127.0.0.1"]),
        ("Env", ["WEB_CONCURRENCY=2"]),
        ("Env", ["PYTHONPATH=/tmp"]),
        ("Env", ["PYTHONHOME=/tmp"]),
        ("Env", ["PATH=x", "PATH=y"]),
        ("Env", ["MISSING_EQUALS"]),
        ("Env", ["=empty"]),
        ("Env", ["BAD NAME=x"]),
        ("Env", [1]),
    ],
)
def test_runtime_configuration_faults(key: str, value: Any) -> None:
    image, service = documents()
    image["config"][key] = value
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize("key,value", [("os", "darwin"), ("architecture", "arm64"), ("config", [])])
def test_image_shape_and_platform_faults(key: str, value: Any) -> None:
    image, service = documents()
    image[key] = value
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize(
    "reference",
    [
        "ghcr.io/example/scanner:latest",
        IMAGE[:-1],
        "ghcr.io/example/scanner@sha256:" + "0" * 64,
        IMAGE + "junk",
    ],
)
def test_mutable_or_malformed_expected_image(reference: str) -> None:
    image, service = documents()
    with pytest.raises(ValueError):
        guard.validate(image, service, reference)


@pytest.mark.parametrize(
    "key,value",
    [
        ("image", IMAGE.replace("ab", "cd")),
        ("command", []),
        ("args", []),
        ("env", []),
        ("envFrom", []),
        ("volumeMounts", []),
        ("securityContext", {}),
        ("ports", [{"containerPort": 8091}]),
        ("livenessProbe", {}),
        ("startupProbe", None),
    ],
)
def test_scanner_overrides_are_rejected(key: str, value: Any) -> None:
    image, service = documents()
    containers(service)[1][key] = value
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize(
    "index,key,value",
    [
        (0, "ports", []),
        (0, "ports", [{"containerPort": 8091}]),
        (0, "ports", [{"containerPort": 8000}, {"containerPort": 8091}]),
        (2, "ports", []),
        (2, "ports", [{"containerPort": 5432}]),
        (1, "name", "api"),
        (1, "name", "unknown"),
        (1, "name", []),
    ],
)
def test_container_names_and_ingress(index: int, key: str, value: Any) -> None:
    image, service = documents()
    containers(service)[index][key] = value
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize(
    "key,value",
    [
        ("httpGet", {"path": "/health", "port": 3310}),
        ("httpGet", {"path": "/ready", "port": 8091}),
        ("httpGet", {"path": "/health", "port": 8091, "httpHeaders": []}),
        ("tcpSocket", {"port": 8091}),
        ("initialDelaySeconds", 1),
        ("initialDelaySeconds", False),
        ("timeoutSeconds", 0),
        ("timeoutSeconds", 6),
        ("periodSeconds", True),
        ("periodSeconds", "5"),
        ("failureThreshold", -1),
        ("failureThreshold", 121),
    ],
)
def test_native_probe_faults(key: str, value: Any) -> None:
    image, service = documents()
    containers(service)[1]["startupProbe"][key] = value
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize(
    "encoded",
    [
        None,
        "{}",
        "not json",
        '{"api":["scanner"]}',
        '{"api":["sql-proxy"]}',
        '{"api":["scanner","sql-proxy"],"scanner":["api"]}',
        '{"api":["scanner","sql-proxy"],"api":["scanner","sql-proxy"]}',
    ],
)
def test_dependency_faults(encoded: Any) -> None:
    image, service = documents()
    service["spec"]["template"]["metadata"]["annotations"][guard.DEPENDENCIES] = encoded
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


def test_missing_container_and_wrong_service_kind() -> None:
    image, service = documents()
    broken = deepcopy(service)
    broken["kind"] = "Job"
    with pytest.raises(ValueError):
        guard.validate(image, broken, IMAGE)
    containers(service).pop()
    with pytest.raises(ValueError):
        guard.validate(image, service, IMAGE)


@pytest.mark.parametrize(
    "bad",
    [None, "not-json", '{"config":{},"config":{}}', "x" * (262144 + 1)],
    # Keep PYTEST_CURRENT_TEST below Linux's per-entry environment limit.
    ids=["missing-file", "invalid-json", "duplicate-config", "oversized-input"],
)
def test_cli_fails_closed_without_echoing_inputs(tmp_path: Path, bad: str | None) -> None:
    image, service = documents()
    image_path, service_path = tmp_path / "image.json", tmp_path / "service.json"
    if bad is not None:
        image_path.write_text(bad)
    service_path.write_text(json.dumps(service))
    result = subprocess.run(
        [
            sys.executable,
            str(GUARD),
            "--image-config",
            str(image_path),
            "--service",
            str(service_path),
            "--scanner-image",
            IMAGE,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stderr == ""
    assert result.stdout == "scanner-launch: FAILED — unverified launch or topology inputs\n"


def test_cli_structural_success(tmp_path: Path) -> None:
    image, service = documents()
    image_path, service_path = tmp_path / "image.json", tmp_path / "service.json"
    image_path.write_text(json.dumps(image))
    service_path.write_text(json.dumps(service))
    result = subprocess.run(
        [
            sys.executable,
            str(GUARD),
            "--image-config",
            str(image_path),
            "--service",
            str(service_path),
            "--scanner-image",
            IMAGE,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0
    assert "structural match only" in result.stdout
