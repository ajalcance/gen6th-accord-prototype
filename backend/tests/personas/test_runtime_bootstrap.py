"""Runtime assembly/configuration evidence only; no network or deployed resources."""

import base64
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from redis_fixtures import service_ca

from accord.config import Settings
from accord.personas.runtime_bootstrap import build_runtime, read_config
from accord.personas.runtime_contracts import GoogleRuntimeConfig, TaskConfig
from accord.personas.runtime_http import configured
from personas.runtime_fixtures import config, task_config


def settings(value: GoogleRuntimeConfig, ca_path: Path | None = None) -> Settings:
    return Settings(
        _env_file=None,
        persona_api_enabled=True,
        persona_photos_enabled=True,
        persona_google_enabled=True,
        persona_workspace_id=value.workspace_id,
        persona_google_config=value.model_dump_json(),
        redis_url="rediss://synthetic-redis:6379/1",
        redis_ca_cert_path=str(ca_path) if ca_path else "",
    )


def test_default_runtime_constructs_no_google_access_or_redis_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create = Mock(side_effect=AssertionError("must remain disconnected"))
    monkeypatch.setattr("accord.personas.runtime_bootstrap.CloudRunAccess", create)
    monkeypatch.setattr("accord.personas.runtime_bootstrap.Redis.from_url", create)
    runtime = build_runtime(Settings(_env_file=None), None, None)
    assert all(value is None for value in (runtime.jobs, runtime.passports, runtime.faces))
    create.assert_not_called()


def test_reviewed_runtime_assembles_all_adapters_without_calling_them(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    value = config()
    signing = value.wrapping_version.replace("wrapping", "signing")
    raw = (
        Ed25519PrivateKey.generate()
        .public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    )
    value = value.model_copy(
        update={
            "signing_version": signing,
            "trusted_signing_keys": {signing: base64.b64encode(raw).decode()},
            "gemini_model": "gemini-synthetic-001",
        }
    )
    monkeypatch.setattr("accord.personas.runtime_bootstrap.sys.platform", "linux")
    monkeypatch.setenv("K_SERVICE", "synthetic-runtime")
    client = AsyncMock()
    create = Mock(return_value=client)
    monkeypatch.setattr("accord.personas.runtime_bootstrap.Redis.from_url", create)
    ca_path = service_ca(tmp_path)
    runtime = build_runtime(settings(value, ca_path), AsyncMock(), AsyncMock())
    assert create.call_args.kwargs["ssl_ca_certs"] == str(ca_path)
    assert create.call_args.kwargs["ssl_cert_reqs"] == "required"
    assert create.call_args.kwargs["ssl_check_hostname"] is True
    assert create.call_args.kwargs["decode_responses"] is False
    assert runtime.jobs and runtime.task_identity and runtime.faces and runtime.similarity
    assert runtime.investigation and runtime.investigation.provider
    ready = configured(value.workspace_id, runtime)
    assert ready.face_jobs_configured and ready.signing_configured and ready.verification_configured
    assert not ready.search_configured and not ready.investigation_configured
    assert not configured(uuid4(), runtime).signing_configured
    client.get.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"persona_api_enabled": False},
        {"persona_photos_enabled": False},
        {"persona_workspace_id": uuid4()},
        {"redis_url": "redis://synthetic-redis:6379/1"},
        {"redis_ca_cert_path": ""},
        {"persona_google_config": "{}"},
    ],
)
def test_partial_activation_config_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, change: dict[str, object]
) -> None:
    monkeypatch.setattr("accord.personas.runtime_bootstrap.sys.platform", "linux")
    monkeypatch.setenv("K_SERVICE", "synthetic-runtime")
    with pytest.raises(ValueError):
        read_config(settings(config(), service_ca(tmp_path)).model_copy(update=change))


@pytest.mark.parametrize(
    "changes",
    [
        {"worker_origin": "https://arbitrary.test"},
        {"queue": "projects/synthetic-project/locations/us-central1/queues/../../other"},
        {"service_email": "job-worker@other-project.iam.gserviceaccount.com"},
        {"service_subject": "user"},
    ],
)
def test_worker_locations_and_identities_are_explicitly_bounded(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        TaskConfig.model_validate({**task_config().model_dump(), **changes})


def test_wrapping_and_signing_keys_and_calibration_cannot_be_substituted() -> None:
    value = config()
    with pytest.raises(ValueError, match="separate"):
        GoogleRuntimeConfig.model_validate(
            {
                **value.model_dump(),
                "signing_version": value.wrapping_version,
                "trusted_signing_keys": {value.wrapping_version: "untrusted"},
            }
        )
    with pytest.raises(ValueError, match="duplicate"):
        GoogleRuntimeConfig.model_validate(
            {**value.model_dump(), "retained_wrapping_versions": [value.wrapping_version]}
        )
