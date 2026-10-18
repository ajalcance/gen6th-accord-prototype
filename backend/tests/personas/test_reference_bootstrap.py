"""Reference config and lazy assembly without browser/scanner/cache activation."""

import hashlib
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from accord.config import DatabaseTransport, Environment, Settings
from accord.personas import reference_bootstrap as reference
from accord.personas.google_access import CloudRunAccess
from accord.personas.runtime_contracts import GoogleRuntimeConfig
from accord.personas.task_google import GoogleTaskDispatcher
from personas.runtime_fixtures import config


def reference_settings(value: GoogleRuntimeConfig) -> Settings:
    return Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        secret_key="synthetic-reference-settings",
        database_transport=DatabaseTransport.CLOUD_SQL_PROXY,
        database_url="postgresql+asyncpg://accord_reference:synthetic@127.0.0.1:5432/appdb",
        persona_google_enabled=True,
        persona_workspace_id=value.workspace_id,
        persona_google_config=value.model_dump_json(),
    )


def platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("accord.personas.reference_bootstrap.sys.platform", "linux")
    monkeypatch.setenv("K_SERVICE", "synthetic-reference")


def test_reference_assembles_only_lazy_job_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    platform(monkeypatch)
    token = AsyncMock(side_effect=AssertionError("assembly must not obtain credentials"))
    monkeypatch.setattr(CloudRunAccess, "token", token)
    value = config().model_copy(update={"gemini_model": "gemini-synthetic-001"})
    settings = reference_settings(value)
    runtime = reference.build_reference(settings)
    assert runtime.jobs.config_id == hashlib.sha256(value.model_dump_json().encode()).hexdigest()
    assert runtime.jobs.workspace_id == value.workspace_id
    assert runtime.identity.config == value.tasks
    assert isinstance(runtime.jobs.dispatcher, GoogleTaskDispatcher)
    assert runtime.jobs.dispatcher.config == value.tasks
    assert not settings.persona_api_enabled and not settings.persona_photos_enabled
    assert not settings.redis_url and not settings.zynth_client_secret
    assert set(runtime.__dataclass_fields__) == {"jobs", "identity"}
    token.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"environment": Environment.DEVELOPMENT},
        {"persona_google_enabled": False},
        {"persona_api_enabled": True},
        {"persona_photos_enabled": True},
        {"database_transport": DatabaseTransport.LOCAL},
        {"database_url": "postgresql+asyncpg://accord_api:synthetic@127.0.0.1:5432/appdb"},
        {"database_url": "postgresql+asyncpg://accord_reference:synthetic@remote:5432/appdb"},
        {"database_url": "postgresql+asyncpg://accord_reference:synthetic@127.0.0.1:5432/other"},
        {"persona_workspace_id": uuid4()},
        {"persona_google_config": ""},
        {"persona_google_config": "{}"},
        {"persona_google_config": "x" * 65537},
    ],
)
def test_reference_configuration_fails_closed_without_exposing_values(
    monkeypatch: pytest.MonkeyPatch, changes: dict[str, object]
) -> None:
    platform(monkeypatch)
    settings = reference_settings(config()).model_copy(update=changes)
    with pytest.raises(ValueError, match="^reviewed production reference configuration required$"):
        reference.build_reference(settings)


@pytest.mark.parametrize("missing", ["linux", "service"])
def test_reference_never_uses_local_credentials(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    platform(monkeypatch)
    if missing == "linux":
        monkeypatch.setattr("accord.personas.reference_bootstrap.sys.platform", "darwin")
    else:
        monkeypatch.delenv("K_SERVICE")
    with pytest.raises(ValueError):
        reference.build_reference(reference_settings(config()))
