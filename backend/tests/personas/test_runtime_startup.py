"""Synthetic startup order/failure acceptance; no database, scanner or cloud calls."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI

import accord.main as main
import accord.personas.runtime_startup as startup
from accord.config import Environment, Settings
from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_scanner import ScanReceipt


def configured(environment: Environment, photos: bool = True, port: int = 3310) -> Settings:
    return Settings(
        _env_file=None,
        environment=environment,
        secret_key="synthetic-startup-fixture",
        database_url="synthetic-unused-database",
        persona_api_enabled=True,
        persona_photos_enabled=photos,
        photo_clamd_port=port,
    )


@pytest.mark.parametrize("environment", [Environment.STAGING, Environment.PRODUCTION])
async def test_inspection_requires_receipt_before_return(
    monkeypatch: pytest.MonkeyPatch, environment: Environment
) -> None:
    probe = AsyncMock(return_value=ScanReceipt("synthetic", "synthetic"))
    monkeypatch.setattr(startup, "probe_scanner", probe)
    await startup.prepare_inspection(configured(environment))
    probe.assert_awaited_once_with()


@pytest.mark.parametrize("environment", list(Environment))
async def test_disabled_inspection_does_not_contact_scanner(
    monkeypatch: pytest.MonkeyPatch, environment: Environment
) -> None:
    probe = AsyncMock(side_effect=AssertionError("unexpected scanner call"))
    monkeypatch.setattr(startup, "probe_scanner", probe)
    await startup.prepare_inspection(configured(environment, photos=False))
    probe.assert_not_awaited()


async def test_development_retains_existing_local_port_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = AsyncMock(side_effect=AssertionError("unexpected scanner call"))
    monkeypatch.setattr(startup, "probe_scanner", probe)
    await startup.prepare_inspection(configured(Environment.DEVELOPMENT, port=3320))
    probe.assert_not_awaited()


@pytest.mark.parametrize("port", [0, 3320, 65536])
async def test_non_development_cannot_probe_a_different_endpoint(
    monkeypatch: pytest.MonkeyPatch, port: int
) -> None:
    probe = AsyncMock()
    monkeypatch.setattr(startup, "probe_scanner", probe)
    with pytest.raises(PhotoUnavailableError, match="^scanner readiness unavailable$"):
        await startup.prepare_inspection(configured(Environment.PRODUCTION, port=port))
    probe.assert_not_awaited()


async def test_failed_receipt_prevents_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        startup, "probe_scanner", AsyncMock(side_effect=PhotoUnavailableError("unavailable"))
    )
    with pytest.raises(PhotoUnavailableError):
        await startup.prepare_inspection(configured(Environment.PRODUCTION))


@pytest.mark.parametrize("failure", [None, "role", "scanner", "cancelled"])
async def test_lifespan_checks_precede_serving_and_always_close_runtime(
    monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    events: list[str] = []

    async def role() -> None:
        events.append("role")
        if failure == "role":
            raise ValueError("role unavailable")

    async def inspection(settings: Settings) -> None:
        assert settings.environment is Environment.PRODUCTION
        events.append("scanner")
        if failure == "scanner":
            raise PhotoUnavailableError("scanner unavailable")
        if failure == "cancelled":
            raise asyncio.CancelledError

    class Runtime:
        async def close(self) -> None:
            events.append("close")

    monkeypatch.setattr(main, "get_settings", lambda: configured(Environment.PRODUCTION))
    monkeypatch.setattr(main, "verify_runtime_role", role)
    monkeypatch.setattr(main, "prepare_inspection", inspection)
    app = FastAPI()
    app.state.persona_runtime = Runtime()

    async def enter() -> None:
        async with main.lifespan(app):
            events.append("serve")

    if failure is None:
        await enter()
        assert events == ["role", "scanner", "serve", "close"]
    else:
        error = {
            "role": ValueError,
            "scanner": PhotoUnavailableError,
            "cancelled": asyncio.CancelledError,
        }[failure]
        with pytest.raises(error):
            await enter()
        assert events == (["role", "close"] if failure == "role" else ["role", "scanner", "close"])
