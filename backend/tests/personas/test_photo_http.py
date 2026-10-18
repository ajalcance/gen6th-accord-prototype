"""ASGI routing/private error contracts, isolated from SQL and runtime configuration."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.photo_contracts import PhotoReceipt, PhotoRejectedError
from accord.personas.photo_http import create_photo_router
from accord.personas.session_boundary import PersonaSession


class Verifier:
    def __init__(self, workspace: UUID) -> None:
        self.workspace = workspace

    async def verify(self, request: Request) -> PersonaSession | None:
        if request.headers.get("x-synthetic-session") != "current":
            return None
        now = datetime.now(UTC)
        return PersonaSession(
            actor_ref="synthetic-human",
            session_id="synthetic-session",
            kind="human",
            workspace_id=self.workspace,
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=1),
        )


async def unbound_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSession() as session:
        yield session


@pytest.mark.asyncio
async def test_upload_session_and_safe_rejection_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = uuid4()
    app = FastAPI()
    app.include_router(create_photo_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db
    calls: list[object] = []

    async def reject(*args: object) -> PhotoReceipt:
        calls.extend(args[:3])
        raise PhotoRejectedError("synthetic private metadata must not escape")

    monkeypatch.setattr("accord.personas.photo_http.intake", reject)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://synthetic") as client:
        path = f"/api/workspaces/{workspace}/personas/photos/upload"
        denied = await client.post(path, json={})
        assert denied.status_code == 401 and not calls
        bad = await client.post(path, json={}, headers={"x-synthetic-session": "current"})
        assert bad.status_code == 422
        assert bad.headers["cache-control"] == "no-store"
        assert "private metadata" not in bad.text
        assert calls[1:3] == [workspace, "synthetic-human"]


@pytest.mark.asyncio
async def test_thumbnail_response_is_private_and_only_for_current_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, version = uuid4(), uuid4()
    app = FastAPI()
    app.include_router(create_photo_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db

    async def pixels(*_args: object) -> bytes:
        return b"synthetic-png"

    monkeypatch.setattr("accord.personas.photo_http.thumbnail", pixels)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/versions/{version}/thumbnail"
        result = await client.get(path, headers={"x-synthetic-session": "current"})
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
        assert result.headers["x-content-type-options"] == "nosniff"
        assert result.headers["content-type"] == "image/png"
        other = await client.get(
            path.replace(str(workspace), str(uuid4())), headers={"x-synthetic-session": "current"}
        )
        assert other.status_code == 401
