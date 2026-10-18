"""Actual private capture routes with synthetic identity and a disconnected database."""

from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas.capture_contracts import CaptureProfile
from accord.personas.photo_http import create_photo_router
from personas.test_photo_http import Verifier, unbound_db


def private_app(workspace: UUID) -> FastAPI:
    app = FastAPI()
    app.include_router(create_photo_router(Verifier(workspace)))
    app.dependency_overrides[get_db] = unbound_db
    return app


def assert_private_image(response: httpx.Response) -> None:
    assert response.status_code == 200 and response.headers["content-type"] == "image/png"
    assert "no-store" in response.headers["cache-control"]
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_capture_read_and_reference_thumbnail_are_private_and_session_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, version, portrait = uuid4(), uuid4(), uuid4()
    calls: list[tuple[object, ...]] = []

    async def profile(*args: object) -> CaptureProfile:
        calls.append(args)
        return CaptureProfile(
            workspace_id=workspace,
            version_id=version,
            upload_id=None,
            portrait_id=None,
            capture=None,
            references=(),
        )

    async def thumbnail(*args: object) -> bytes:
        calls.append(args)
        return b"\x89PNG\r\n\x1a\nsynthetic"

    monkeypatch.setattr("accord.personas.capture_http.capture_profile", profile)
    monkeypatch.setattr("accord.personas.capture_http.reference_thumbnail", thumbnail)
    app = private_app(workspace)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos"
        assert (await client.post(f"{path}/capture/query", json={})).status_code == 401
        assert not calls
        headers = {"x-synthetic-session": "current"}
        ok = await client.post(
            f"{path}/capture/query", json={"version_id": str(version)}, headers=headers
        )
        assert ok.status_code == 200 and ok.headers["cache-control"] == "no-store"
        assert ok.json()["recognition"] == "not_processed" and "ciphertext" not in ok.text
        invalid = await client.post(f"{path}/capture/query", json={}, headers=headers)
        assert invalid.status_code == 422 and len(calls) == 1
        image = await client.get(
            f"{path}/versions/{version}/references/{portrait}/thumbnail", headers=headers
        )
        assert_private_image(image)
        assert calls[0][2] == "synthetic-human" and calls[1][2] == "synthetic-human"
        foreign = await client.post(
            path.replace(str(workspace), str(uuid4())) + "/capture/query",
            json={"version_id": str(version)},
            headers=headers,
        )
        assert foreign.status_code == 401 and len(calls) == 2
