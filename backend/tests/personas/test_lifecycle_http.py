"""Real ASGI boundary requests with synthetic sessions; no runtime identity acceptance."""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas import lifecycle_service as service
from accord.personas.lifecycle_http import create_lifecycle_router
from accord.personas.repository import AccessDeniedError
from personas.lifecycle_fixtures import command, receipt
from personas.test_photo_http import Verifier, unbound_db


def app(workspace: UUID, enabled: bool = True) -> FastAPI:
    result = FastAPI()
    result.include_router(create_lifecycle_router(Verifier(workspace), enabled))
    result.dependency_overrides[get_db] = unbound_db
    return result


@pytest.mark.asyncio
async def test_disabled_missing_and_foreign_sessions_never_append(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, append = uuid4(), AsyncMock()
    monkeypatch.setattr(service, "append", append)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app(workspace, False)), base_url="http://fixture"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/lifecycle/append"
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
    append.assert_not_called()


@pytest.mark.asyncio
async def test_authorisation_precedes_parsing_and_receipt_is_private(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("accord.personas.credit_intent.authorize_actor", AsyncMock())
    monkeypatch.setattr("accord.personas.credit_intent.observation", Mock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    c, workspace = command(), uuid4()
    append = AsyncMock(return_value=receipt(c, workspace, actor="synthetic-human"))
    monkeypatch.setattr(service, "append", append)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app(workspace)), base_url="http://fixture"
    ) as client:
        path, headers = f"/api/workspaces/{workspace}/personas/lifecycle/append", {
            "x-synthetic-session": "current"
        }
        response = await client.post(path, json=c.model_dump(mode="json"), headers=headers)
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert append.await_args is not None
        assert append.await_args.args[2].actor_ref == "synthetic-human"
        assert (await client.post(path, content=" " * 12289, headers=headers)).status_code == 422
        assert (
            await client.post(
                path, json={**c.model_dump(mode="json"), "verified": True}, headers=headers
            )
        ).status_code == 422
        monkeypatch.setattr(
            "accord.personas.credit_intent.authorize_actor",
            AsyncMock(side_effect=AccessDeniedError("denied")),
        )
        assert (await client.post(path, content="not-json", headers=headers)).status_code == 403
    assert append.await_count == 1
