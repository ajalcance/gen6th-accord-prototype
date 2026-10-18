"""Actual ASGI session/private boundaries, with synthetic service result and disconnected SQL."""

from uuid import uuid4

import httpx
import pytest

from accord.personas.face_contracts import FaceProfile
from personas.test_capture_http import private_app


@pytest.mark.asyncio
async def test_private_face_query_session_binding_and_provider_outage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, version, portrait = uuid4(), uuid4(), uuid4()
    calls: list[str] = []

    async def profile(*args: object) -> FaceProfile:
        calls.append(str(args[2]))
        return FaceProfile(
            workspace_id=workspace,
            version_id=version,
            portrait_id=portrait,
            latest=None,
            provider_ready=False,
        )

    async def unavailable(*args: object) -> None:
        raise RuntimeError("provider-sensitive-detail")

    monkeypatch.setattr("accord.personas.face_http.profile", profile)
    monkeypatch.setattr("accord.personas.face_http.process", unavailable)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(workspace)), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/faces"
        payload = {"version_id": str(version), "portrait_id": str(portrait)}
        assert (await client.post(f"{path}/query", json=payload)).status_code == 401
        assert not calls
        headers = {"x-synthetic-session": "current"}
        ok = await client.post(f"{path}/query", json=payload, headers=headers)
        assert ok.status_code == 200 and ok.json()["provider_ready"] is False
        assert ok.headers["cache-control"] == "no-store" and calls == ["synthetic-human"]
        bad = await client.post(
            f"{path}/process",
            json={**payload, "request_id": str(uuid4()), "actor_ref": "forged"},
            headers=headers,
        )
        assert bad.status_code == 422
        failed = await client.post(
            f"{path}/process", json={**payload, "request_id": str(uuid4())}, headers=headers
        )
        assert failed.status_code == 503 and "provider-sensitive-detail" not in failed.text
        assert failed.headers["cache-control"] == "no-store"
