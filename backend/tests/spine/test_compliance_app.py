"""Health-only factory, fail-closed startup and owned Redis cleanup; synthetic dependencies."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from redis_fixtures import service_ca

from accord.command import compliance_app as module
from accord.command.compliance_config import validate_compliance
from accord.config import DatabaseTransport, Environment, Settings


def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setattr("accord.command.compliance_config.sys.platform", "linux")
    monkeypatch.setenv("CLOUD_RUN_WORKER_POOL", "synthetic-compliance")
    return Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        secret_key="synthetic-worker-settings",
        database_transport=DatabaseTransport.CLOUD_SQL_PROXY,
        database_url="postgresql+asyncpg://accord_compliance:synthetic@127.0.0.1:5432/appdb",
        redis_url="rediss://synthetic-redis:6378/0",
        redis_ca_cert_path=str(service_ca(tmp_path)),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"environment": Environment.DEVELOPMENT},
        {"database_transport": DatabaseTransport.LOCAL},
        {"database_url": "postgresql+asyncpg://accord_api:synthetic@127.0.0.1:5432/appdb"},
        {"persona_api_enabled": True},
        {"persona_photos_enabled": True},
        {"persona_google_enabled": True},
        {"redis_url": "redis://synthetic-redis:6378/0"},
        {"redis_ca_cert_path": ""},
        {"command_poll_seconds": 0},
        {"command_poll_seconds": 11},
        {"command_poll_seconds": float("nan")},
        {"command_poll_seconds": float("inf")},
    ],
)
def test_invalid_configuration_never_exposes_private_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changes: dict[str, object]
) -> None:
    settings = configured(tmp_path, monkeypatch).model_copy(update=changes)
    with pytest.raises(ValueError, match="^reviewed production compliance configuration required$"):
        validate_compliance(settings)


@pytest.mark.parametrize("missing", ["linux", "worker_pool"])
def test_wrong_platform_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    settings = configured(tmp_path, monkeypatch)
    if missing == "linux":
        monkeypatch.setattr("accord.command.compliance_config.sys.platform", "darwin")
    else:
        monkeypatch.delenv("CLOUD_RUN_WORKER_POOL")
    with pytest.raises(ValueError):
        validate_compliance(settings)


@pytest.mark.parametrize("failure", [None, "role", "pass", "cancel", "timeout"])
async def test_startup_health_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    settings = configured(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "get_settings", lambda: settings)
    role = AsyncMock(side_effect=RuntimeError("private-role") if failure == "role" else None)
    run = AsyncMock(return_value=(0, 0, 0))
    if failure == "pass":
        run.side_effect = RuntimeError("private-pass")
    if failure == "cancel":
        run.side_effect = asyncio.CancelledError
    if failure == "timeout":
        monkeypatch.setattr(module, "STARTUP_SECONDS", 0.01)

        async def blocked() -> None:
            await asyncio.Event().wait()

        role.side_effect = blocked
    redis = AsyncMock()
    monkeypatch.setattr(module, "verify_compliance_role", role)
    monkeypatch.setattr(module, "run_once", run)
    monkeypatch.setattr(module, "get_redis", lambda: redis)
    app = module.create_compliance_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        assert (await client.get("/health")).status_code == 503
        await lifecycle(app, client, failure)
        assert (await client.get("/health")).json()["status"] == "stopping"
    role.assert_awaited_once()
    if failure in {"role", "timeout"}:
        run.assert_not_awaited()
        redis.aclose.assert_not_awaited()
    else:
        redis.aclose.assert_awaited_once()


async def lifecycle(app: FastAPI, client: httpx.AsyncClient, failure: str | None) -> None:
    if failure is None:
        async with app.router.lifespan_context(app):
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "progressing", "scope": "worker_pass_progress"}
            assert response.headers["cache-control"] == "no-store"
            for path in ("/", "/docs", "/openapi.json", "/api", "/internal/personas/jobs/execute"):
                assert (await client.post(path)).status_code == 404
    else:
        with pytest.raises(asyncio.CancelledError if failure == "cancel" else RuntimeError):
            async with app.router.lifespan_context(app):
                pytest.fail("failed startup must not yield")


@pytest.mark.parametrize("failure", [False, True])
async def test_role_verification_disposes_its_startup_pool(
    monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    engine = AsyncMock()
    monkeypatch.setattr("accord.command.compliance_app.connection._engine", engine)
    role = AsyncMock(side_effect=RuntimeError("unsafe") if failure else None)
    monkeypatch.setattr(module, "verify_runtime_role", role)
    if failure:
        with pytest.raises(RuntimeError, match="unsafe"):
            await module.verify_compliance_role()
    else:
        await module.verify_compliance_role()
    engine.dispose.assert_awaited_once()


async def test_redis_close_is_bounded_and_has_no_private_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = AsyncMock()
    redis.aclose.side_effect = RuntimeError("private-connection-detail")
    with pytest.raises(RuntimeError, match="^compliance Redis cleanup unavailable$"):
        await module.close_redis(redis)
    monkeypatch.setattr(module, "CLOSE_SECONDS", 0.01)

    async def blocked() -> None:
        await asyncio.Event().wait()

    redis.aclose.side_effect = blocked
    with pytest.raises(RuntimeError, match="^compliance Redis cleanup unavailable$"):
        await module.close_redis(redis)


async def test_role_timeout_still_disposes_startup_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "ROLE_SECONDS", 0.01)
    engine = AsyncMock()
    monkeypatch.setattr("accord.command.compliance_app.connection._engine", engine)

    async def blocked() -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(module, "verify_runtime_role", blocked)
    with pytest.raises(TimeoutError):
        await module.verify_compliance_role()
    engine.dispose.assert_awaited_once()


async def test_http_health_tracks_failure_staleness_and_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = configured(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(module, "verify_compliance_role", AsyncMock())
    monkeypatch.setattr(module, "get_redis", AsyncMock)
    run = AsyncMock(return_value=(0, 0, 0))
    monkeypatch.setattr(module, "run_once", run)
    app = module.create_compliance_app()
    now = [100.0]
    app.state.compliance.clock = lambda: now[0]
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
        ) as client:
            now[0] += 100
            assert (await client.get("/health")).json()["status"] == "stalled"
            assert (await client.get("/health")).status_code == 503
            run.side_effect = RuntimeError("private-detail")
            with pytest.raises(RuntimeError):
                await app.state.compliance.cycle()
            response = await client.get("/health")
            assert response.status_code == 503 and response.json()["status"] == "failed"
            assert "private-detail" not in response.text
            run.side_effect = None
            await app.state.compliance.cycle()
            assert (await client.get("/health")).status_code == 200
