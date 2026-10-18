"""Actual route and private failure contracts; identity is explicitly synthetic here."""

from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas.photo_contracts import PhotoRejectedError
from accord.personas.photo_http import create_photo_router
from accord.personas.portrait_search import PortraitSearchPage
from accord.personas.workflow_contracts import WorkflowActor
from personas.test_photo_http import Verifier, unbound_db
from personas.test_portrait_search import page


@pytest.mark.asyncio
async def test_actual_search_route_is_session_scoped_and_private(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = uuid4()
    result = page(workspace)
    calls: list[object] = []

    async def search(*args: object) -> PortraitSearchPage:
        calls.extend(args)
        return result

    monkeypatch.setattr("accord.personas.portrait_search_http.search_portraits", search)
    app = FastAPI()
    app.include_router(create_photo_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/search"
        assert (await client.post(path, json={})).status_code == 401
        assert not calls
        headers = {"x-synthetic-session": "current"}
        ok = await client.post(path, json={}, headers=headers)
        assert ok.status_code == 200 and ok.json() == result.model_dump(mode="json")
        assert ok.headers["cache-control"] == "no-store"
        assert calls[1] == workspace and isinstance(calls[2], WorkflowActor)
        assert calls[2].actor_ref == "synthetic-human"
        foreign = await client.post(
            path.replace(str(workspace), str(uuid4())), json={}, headers=headers
        )
        assert foreign.status_code == 401 and len(calls) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("error,status", [(PhotoRejectedError, 422), (RuntimeError, 503)])
async def test_search_errors_do_not_expose_private_input(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception], status: int
) -> None:
    workspace = uuid4()

    async def fail(*_args: object) -> PortraitSearchPage:
        raise error("synthetic private filename and provider detail")

    monkeypatch.setattr("accord.personas.portrait_search_http.search_portraits", fail)
    app = FastAPI()
    app.include_router(create_photo_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        response = await client.post(
            f"/api/workspaces/{workspace}/personas/photos/search",
            json={},
            headers={"x-synthetic-session": "current"},
        )
    assert response.status_code == status and "private filename" not in response.text
    assert response.headers["cache-control"] == "no-store"
