"""Private, disabled-by-default routes with actual ASGI requests and synthetic sessions."""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas import credit_service as service
from accord.personas.credit_contracts import CreditProfile
from accord.personas.credit_http import create_credit_router
from accord.personas.repository import AccessDeniedError
from personas.test_credit_contracts import declaration, profile
from personas.test_photo_http import Verifier, unbound_db


def app(workspace: UUID, enabled: bool = True) -> FastAPI:
    result = FastAPI()
    result.include_router(create_credit_router(Verifier(workspace), enabled))
    result.dependency_overrides[get_db] = unbound_db
    return result


def authorize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("accord.personas.credit_intent.authorize_actor", AsyncMock())
    monkeypatch.setattr("accord.personas.credit_intent.observation", Mock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())


@pytest.mark.asyncio
async def test_disabled_routes_and_missing_or_foreign_sessions_never_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = uuid4()
    save = AsyncMock()
    monkeypatch.setattr(service, "save", save)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app(workspace, False)), base_url="http://fixture"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/credits/save"
        assert (await client.post(path, json={})).status_code == 401
        assert (
            await client.post(path, json={}, headers={"x-synthetic-session": "current"})
        ).status_code == 503
        assert (
            await client.post(
                path.replace(str(workspace), str(uuid4())),
                json={},
                headers={"x-synthetic-session": "current"},
            )
        ).status_code == 401
    save.assert_not_called()


@pytest.mark.asyncio
async def test_save_response_and_read_are_private_and_server_attributed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorize(monkeypatch)
    receipt, c = profile(), declaration()
    receipt = receipt.model_copy(update={"version_id": c.version_id, "request_id": c.request_id})
    save = AsyncMock(return_value=receipt)
    monkeypatch.setattr(service, "save", save)
    monkeypatch.setattr(
        service,
        "read",
        AsyncMock(
            return_value=CreditProfile(
                workspace_id=receipt.workspace_id, version_id=c.version_id, snapshot=receipt
            )
        ),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app(receipt.workspace_id)), base_url="http://fixture"
    ) as client:
        path = f"/api/workspaces/{receipt.workspace_id}/personas/credits"
        headers = {"x-synthetic-session": "current"}
        response = await client.post(
            path + "/save", json=c.model_dump(mode="json"), headers=headers
        )
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert (
            save.await_args is not None and save.await_args.args[2].actor_ref == "synthetic-human"
        )
        assert (
            await client.post(
                path + "/read", json={"version_id": str(c.version_id)}, headers=headers
            )
        ).status_code == 200
        assert (
            await client.post(
                path + "/save",
                json={**c.model_dump(mode="json"), "confirmed": True},
                headers=headers,
            )
        ).status_code == 422
        assert (
            await client.post(path + "/save", content=" " * 12289, headers=headers)
        ).status_code == 422
        assert save.await_count == 1


@pytest.mark.asyncio
async def test_denied_membership_precedes_invalid_body(monkeypatch: pytest.MonkeyPatch) -> None:
    authorize(monkeypatch)
    monkeypatch.setattr(
        "accord.personas.credit_intent.authorize_actor",
        AsyncMock(side_effect=AccessDeniedError("denied")),
    )
    workspace = uuid4()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app(workspace)), base_url="http://fixture"
    ) as client:
        response = await client.post(
            f"/api/workspaces/{workspace}/personas/credits/save",
            content="not json",
            headers={"x-synthetic-session": "current"},
        )
    assert response.status_code == 403 and "denied" in response.text
