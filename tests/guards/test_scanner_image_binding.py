"""Content binding fault tests; synthetic OCI bytes exist only in these tests."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

DIRECTORY = Path(__file__).parent
if not (DIRECTORY / "scanner_image_binding.py").is_file():
    DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(DIRECTORY))
SPEC = importlib.util.spec_from_file_location(
    "scanner_binding_candidate", DIRECTORY / "scanner_image_binding.py"
)
assert SPEC is not None and SPEC.loader is not None
binding = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(binding)


def inputs() -> tuple[bytes, dict[str, Any]]:
    config = json.dumps(
        {
            "os": "linux",
            "architecture": "amd64",
            "config": {
                "User": "100",
                "Cmd": list(binding.launch.COMMAND),
                "Env": [],
            },
        }
    ).encode()
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": "sha256:" + hashlib.sha256(config).hexdigest(),
            "size": len(config),
        },
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": "sha256:" + "ab" * 32,
                "size": 123,
            }
        ],
    }
    return config, manifest


def encode(manifest: dict[str, Any]) -> tuple[bytes, str]:
    data = json.dumps(manifest, separators=(",", ":")).encode()
    return data, "ghcr.io/example/test-only-scanner@sha256:" + hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("docker", [False, True])
def test_single_manifest_binds_exact_config(docker: bool) -> None:
    config, manifest = inputs()
    if docker:
        manifest["mediaType"] = "application/vnd.docker.distribution.manifest.v2+json"
        manifest["config"]["mediaType"] = "application/vnd.docker.container.image.v1+json"
        manifest["layers"][0]["mediaType"] = "application/vnd.docker.image.rootfs.diff.tar.gzip"
    data, reference = encode(manifest)
    assert binding.bind(data, config, reference) == json.loads(config)


def test_expected_digest_cannot_be_replaced_by_supplied_manifest() -> None:
    config, manifest = inputs()
    data, reference = encode(manifest)
    for changed in (data + b" ", data[:-1], b"{}"):
        with pytest.raises(ValueError, match="manifest does not match"):
            binding.bind(changed, config, reference)


@pytest.mark.parametrize("change", ["bytes", "size", "digest"])
def test_configuration_binding_faults(change: str) -> None:
    config, manifest = inputs()
    if change == "bytes":
        config += b" "
    elif change == "size":
        manifest["config"]["size"] += 1
    else:
        manifest["config"]["digest"] = "sha256:" + "cd" * 32
    data, reference = encode(manifest)
    with pytest.raises(ValueError, match="configuration does not match"):
        binding.bind(data, config, reference)


@pytest.mark.parametrize(
    "key,value",
    [
        ("schemaVersion", True),
        ("schemaVersion", 1),
        ("schemaVersion", "2"),
        ("mediaType", "application/vnd.oci.image.index.v1+json"),
        ("mediaType", "application/vnd.docker.distribution.manifest.list.v2+json"),
        ("mediaType", None),
        ("manifests", []),
        ("subject", {}),
        ("artifactType", "test"),
        ("layers", []),
        ("layers", None),
        ("layers", [{}] * 129),
        ("config", None),
    ],
)
def test_manifest_shape_faults(key: str, value: Any) -> None:
    config, manifest = inputs()
    manifest[key] = value
    data, reference = encode(manifest)
    with pytest.raises(ValueError):
        binding.bind(data, config, reference)


@pytest.mark.parametrize("where", ["config", "layer"])
@pytest.mark.parametrize(
    "key,value",
    [
        ("mediaType", "wrong"),
        ("digest", "sha256:abc"),
        ("digest", None),
        ("size", True),
        ("size", 0),
        ("size", -1),
        ("size", "1"),
        ("urls", []),
        ("data", "embedded"),
    ],
)
def test_descriptor_faults(where: str, key: str, value: Any) -> None:
    config, manifest = inputs()
    target = manifest["config"] if where == "config" else manifest["layers"][0]
    target[key] = value
    data, reference = encode(manifest)
    with pytest.raises(ValueError):
        binding.bind(data, config, reference)


def test_duplicate_fields_and_oversized_inputs() -> None:
    config, manifest = inputs()
    data, reference = encode(manifest)
    duplicate = data[:-1] + b',"schemaVersion":2}'
    duplicate_reference = (
        "ghcr.io/example/test-only-scanner@sha256:" + hashlib.sha256(duplicate).hexdigest()
    )
    with pytest.raises(ValueError, match="duplicate JSON"):
        binding.bind(duplicate, config, duplicate_reference)
    for manifest_data, config_data in [
        (b"", config),
        (data, b""),
        (b"x" * (binding.MANIFEST_LIMIT + 1), config),
        (data, b"x" * (binding.launch.LIMIT + 1)),
    ]:
        with pytest.raises(ValueError, match="missing or oversized"):
            binding.bind(manifest_data, config_data, reference)


def service(reference: str) -> dict[str, Any]:
    return {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {binding.launch.DEPENDENCIES: '{"api":["scanner","sql-proxy"]}'}
                },
                "spec": {
                    "containers": [
                        {"name": "api", "ports": [{"containerPort": 8000}]},
                        {
                            "name": "scanner",
                            "image": reference,
                            "startupProbe": {
                                "httpGet": {"path": "/health", "port": 8091},
                                "timeoutSeconds": 2,
                                "periodSeconds": 5,
                                "failureThreshold": 30,
                            },
                        },
                        {"name": "sql-proxy"},
                    ]
                },
            },
        },
    }


@pytest.mark.parametrize("fault", [None, "manifest", "config", "launch", "service"])
def test_cli_binding_and_launch_fail_closed(tmp_path: Path, fault: str | None) -> None:
    config, manifest = inputs()
    if fault == "launch":
        document = json.loads(config)
        document["config"]["User"] = "0"
        config = json.dumps(document).encode()
        manifest["config"].update(
            digest="sha256:" + hashlib.sha256(config).hexdigest(), size=len(config)
        )
    data, reference = encode(manifest)
    document = service(reference)
    if fault == "service":
        document["spec"]["template"]["spec"]["containers"][1]["image"] = reference + "wrong"
    paths = [tmp_path / name for name in ("manifest.json", "config.json", "service.json")]
    paths[0].write_bytes(data + (b" " if fault == "manifest" else b""))
    paths[1].write_bytes(config + (b" " if fault == "config" else b""))
    paths[2].write_text(json.dumps(document))
    result = subprocess.run(
        [
            sys.executable,
            str(DIRECTORY / "scanner_image_binding.py"),
            "--manifest",
            str(paths[0]),
            "--image-config",
            str(paths[1]),
            "--service",
            str(paths[2]),
            "--scanner-image",
            reference,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == (0 if fault is None else 1)
    assert result.stderr == ""
    if fault is not None:
        assert result.stdout == "scanner-image-binding: FAILED — image or launch input mismatch\n"
    else:
        assert "digest chain and launch structure only" in result.stdout


@pytest.mark.parametrize("missing", ["MANIFEST", "CONFIG", "SERVICE", "IMAGE"])
def test_make_gate_requires_every_input(missing: str) -> None:
    values = {name: "unused" for name in ("MANIFEST", "CONFIG", "SERVICE", "IMAGE")}
    values[missing] = ""
    result = subprocess.run(
        ["make", "scanner-launch-check", *(f"SCANNER_{k}={v}" for k, v in values.items())],
        cwd=DIRECTORY.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0
    assert "all four artifact inputs are required" in result.stdout
    assert "digest chain" not in result.stdout


@pytest.mark.parametrize("fault", [None, "digest", "command", "ingress"])
def test_make_gate_checks_actual_bound_inputs(tmp_path: Path, fault: str | None) -> None:
    config, manifest = inputs()
    if fault == "command":
        document = json.loads(config)
        document["config"]["Cmd"] += ["--reload"]
        config = json.dumps(document).encode()
        manifest["config"].update(
            digest="sha256:" + hashlib.sha256(config).hexdigest(), size=len(config)
        )
    data, reference = encode(manifest)
    document = service(reference)
    if fault == "ingress":
        document["spec"]["template"]["spec"]["containers"][1]["ports"] = [{"containerPort": 8091}]
    paths = [tmp_path / name for name in ("manifest.json", "config.json", "service.json")]
    paths[0].write_bytes(data + (b" " if fault == "digest" else b""))
    paths[1].write_bytes(config)
    paths[2].write_text(json.dumps(document))
    result = subprocess.run(
        [
            "make",
            "scanner-launch-check",
            f"SCANNER_PYTHON={sys.executable}",
            f"SCANNER_MANIFEST={paths[0]}",
            f"SCANNER_CONFIG={paths[1]}",
            f"SCANNER_SERVICE={paths[2]}",
            f"SCANNER_IMAGE={reference}",
        ],
        cwd=DIRECTORY.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == (0 if fault is None else 2)
    if fault is None:
        assert "digest chain and launch structure only" in result.stdout
        assert "structural match only" in result.stdout
    else:
        assert "scanner-image-binding: FAILED" in result.stdout
        assert "scanner-launch: checked" not in result.stdout
