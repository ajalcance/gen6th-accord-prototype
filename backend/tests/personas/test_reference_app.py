"""Actual narrowed factory with synthetic signed OIDC and disconnected SQL."""

from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from accord.db.connection import get_db
from accord.personas import job_worker, reference_app
from accord.personas.reference_bootstrap import build_reference
from accord.personas.task_identity import GoogleTaskIdentity
from personas.runtime_fixtures import config
from personas.test_photo_http import unbound_db
from personas.test_reference_bootstrap import platform, reference_settings
from personas.test_task_identity import material


@pytest.mark.parametrize("failure", [False, True])
async def test_factory_awaits_role_guard_before_serving(
    monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    platform(monkeypatch)
    monkeypatch.setattr(reference_app, "get_settings", lambda: reference_settings(config()))
    guard = AsyncMock(side_effect=RuntimeError("unsafe SQL role") if failure else None)
    monkeypatch.setattr(reference_app, "verify_runtime_role", guard)
    app = reference_app.create_reference_app()
    if failure:
        with pytest.raises(RuntimeError, match="unsafe SQL role"):
            async with app.router.lifespan_context(app):
                pytest.fail("startup must not yield")
    else:
        async with app.router.lifespan_context(app):
            guard.assert_awaited_once()
    guard.assert_awaited_once()


@pytest.mark.parametrize("claims", [{}, {"aud": "https://other.run.app"}, {"sub": "other"}])
async def test_reference_factory_preserves_real_signed_machine_boundary(
    monkeypatch: pytest.MonkeyPatch, claims: dict[str, object]
) -> None:
    platform(monkeypatch)
    value = config()
    settings = reference_settings(value)
    runtime = build_reference(settings)
    token, key = material(claims)
    identity = GoogleTaskIdentity(
        value.tasks, httpx.MockTransport(lambda _: httpx.Response(200, json={"keys": [key]}))
    )
    monkeypatch.setattr(reference_app, "get_settings", lambda: settings)
    monkeypatch.setattr(
        reference_app, "build_reference", lambda _: type(runtime)(runtime.jobs, identity)
    )
    execute = AsyncMock()
    reconcile = AsyncMock(return_value={"examined": 0, "dispatched": 0})
    monkeypatch.setattr(job_worker, "execute", execute)
    monkeypatch.setattr(job_worker, "reconcile", reconcile)
    app = reference_app.create_reference_app()
    app.dependency_overrides[get_db] = unbound_db
    payload = {
        "workspace_id": str(value.workspace_id),
        "job_id": str(uuid4()),
        "dispatch_id": str(uuid4()),
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200 and set(response.json()) == {"status", "version"}
        for route in ("execute", "reconcile"):
            path = "/internal/personas/jobs/" + route
            assert (
                await client.post(path, headers={"x-cloudtasks-taskname": "claimed"})
            ).status_code == 401
            response = await client.post(
                path, json=payload, headers={"Authorization": "Bearer " + token}
            )
            assert response.status_code == (401 if claims else 200)
            assert response.headers["cache-control"] == "no-store"
    if claims:
        execute.assert_not_awaited()
        reconcile.assert_not_awaited()
    else:
        assert execute.await_args and execute.await_args.args[-1] == value.tasks.service_email
        assert reconcile.await_args and reconcile.await_args.args[-1] == value.tasks.service_email


async def test_reference_factory_has_no_browser_api_or_discovery_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    platform(monkeypatch)
    monkeypatch.setattr(reference_app, "get_settings", lambda: reference_settings(config()))
    app = reference_app.create_reference_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        for path in (
            "/",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/api/workspaces/anything/personas/jobs/enqueue",
            "/p/anything",
        ):
            assert (await client.get(path)).status_code == 404
            assert (await client.post(path)).status_code == 404
