"""Actual ASGI routes; missing sessions, malformed packages and failures stay private."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas import passport_http as api
from accord.personas import passport_service as service
from accord.personas.passport_contracts import (
    AssetPage,
    PassportPayload,
    PassportReadiness,
    PassportVerification,
    SignedPassport,
)
from accord.personas.repository import AccessDeniedError
from personas.passport_fixtures import material, runtime, signed
from personas.test_photo_http import Verifier, unbound_db


async def http_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FastAPI, PassportPayload, SignedPassport, AsyncMock]:
    payload, _ = material()
    workspace, campaign = payload.version.workspace_id, payload.campaign.id
    package = await signed(payload, runtime())
    monkeypatch.setattr(api, "authorize_actor", AsyncMock())
    monkeypatch.setattr(api, "observation", Mock())
    monkeypatch.setattr(
        service,
        "readiness",
        AsyncMock(
            return_value=PassportReadiness(
                workspace_id=workspace, export_available=False, verification_available=False
            )
        ),
    )
    export = AsyncMock(return_value=package)
    monkeypatch.setattr(service, "export", export)
    monkeypatch.setattr(
        service,
        "verify",
        AsyncMock(
            return_value=PassportVerification(
                workspace_id=workspace, campaign_id=campaign, integrity="invalid_signature"
            )
        ),
    )
    monkeypatch.setattr(
        "accord.personas.passport_repository.assets",
        AsyncMock(
            return_value=AssetPage(
                workspace_id=workspace, version_id=payload.version.version_id, assets=()
            )
        ),
    )
    app = FastAPI()
    app.include_router(api.create_passport_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db
    return app, payload, package, export


@pytest.mark.asyncio
async def test_private_session_bound_routes_reject_duplicate_keys_and_unbounded_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, payload, package, export = await http_material(monkeypatch)
    workspace, campaign = payload.version.workspace_id, payload.campaign.id
    path = f"/api/workspaces/{workspace}/personas/passports"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        for route in ("readiness", "assets", "export", "verify"):
            assert (await client.post(f"{path}/{route}", json={})).status_code == 401
        headers = {"x-synthetic-session": "current"}
        for route, body in (
            ("readiness", {}),
            ("assets", {"version_id": str(payload.version.version_id)}),
            ("export", {"campaign_id": str(campaign)}),
            ("verify", {"campaign_id": str(campaign), "package": package.model_dump(mode="json")}),
        ):
            response = await client.post(f"{path}/{route}", json=body, headers=headers)
            assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        for invalid_bytes in (b'{"campaign_id":"one","campaign_id":"two"}', b"x" * 65537):
            assert (
                await client.post(f"{path}/export", content=invalid_bytes, headers=headers)
            ).status_code == 422
        assert (
            await client.post(
                f"{path}/export",
                json={"campaign_id": str(campaign), "actor_ref": "browser"},
                headers=headers,
            )
        ).status_code == 422
        assert export.await_count == 1


@pytest.mark.asyncio
async def test_membership_denial_precedes_body_and_provider_errors_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = uuid4()
    authorization = AsyncMock(side_effect=AccessDeniedError("private denial"))
    monkeypatch.setattr(api, "authorize_actor", authorization)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    monkeypatch.setattr(api, "observation", Mock())
    exporter = AsyncMock(side_effect=RuntimeError("private key provider content"))
    monkeypatch.setattr(service, "export", exporter)
    app = FastAPI()
    app.include_router(api.create_passport_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/passports/export"
        headers = {"x-synthetic-session": "current"}
        assert (await client.post(path, content=b"invalid", headers=headers)).status_code == 403
        exporter.assert_not_called()
        authorization.side_effect = None
        failed = await client.post(path, json={"campaign_id": str(uuid4())}, headers=headers)
        assert failed.status_code == 503 and "private key" not in failed.text
