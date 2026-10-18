"""Synthetic HTTP/lifespan only: no native platform or real process acceptance."""

import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from accord.personas.photo_scanner import ScanReceipt
from accord.scanner import app as module
from personas.scanner_fixtures import SyntheticRuntime


def test_no_automatic_image_or_runtime_is_selected() -> None:
    import inspect

    assert (
        inspect.signature(module.create_scanner_app).parameters["runtime"].default
        is inspect.Parameter.empty
    )


@pytest.mark.parametrize("platform,uid", [("darwin", 100), ("linux", 0)])
def test_factory_denies_unsupported_platform_or_root(
    platform: str, uid: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("accord.scanner.app.sys.platform", platform)
    monkeypatch.setattr("accord.scanner.app.os.geteuid", lambda: uid)
    with pytest.raises(ValueError, match="^scanner platform unavailable$"):
        module.create_scanner_app(SyntheticRuntime())


async def test_health_starting_ready_failure_stopping_and_no_other_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("accord.scanner.app.sys.platform", "linux")
    monkeypatch.setattr("accord.scanner.app.os.geteuid", lambda: 100)
    runtime, ready = SyntheticRuntime(), asyncio.Event()
    runtime.prepare_gate = asyncio.Event()
    app = module.create_scanner_app(runtime)

    async def probe() -> ScanReceipt:
        ready.set()
        return ScanReceipt("ClamAV 1.4.3", "12345")

    app.state.scanner.probe = probe
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        assert (await c.get("/health")).status_code == 503
        async with app.router.lifespan_context(app):
            assert (await c.get("/health")).json()["status"] == "starting"
            runtime.prepare_gate.set()
            await asyncio.wait_for(ready.wait(), 1)
            response = await c.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ready", "scope": "scanner_protocol_freshness"}
            assert response.headers["Cache-Control"] == "no-store"
            app.state.scanner.probe = AsyncMock(side_effect=RuntimeError("private"))
            await app.state.scanner.check()
            assert (await c.get("/health")).status_code == 503
            for path in ("/docs", "/openapi.json", "/scan", "/tasks", "/config"):
                assert (await c.get(path)).status_code == 404
            assert (await c.post("/health", json={"command": "SCAN"})).status_code == 405
        assert (await c.get("/health")).json()["status"] == "stopping"
    assert all(child.returncode is not None for child in runtime.children)
