"""Actual routes with synthetic sessions; backend failures remain private and sanitized."""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import httpx
import pytest

from accord.personas import investigation_service as service
from accord.personas.investigation_contracts import InvestigationPage, InvestigationReadiness
from accord.personas.repository import AccessDeniedError
from personas.investigation_fixtures import command, result
from personas.test_capture_http import private_app


@pytest.mark.asyncio
async def test_all_routes_require_session_and_bound_metadata_before_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, intent = uuid4(), command()
    packet = result(workspace, intent)
    generate = AsyncMock(return_value=packet)
    monkeypatch.setattr(service, "generate", generate)
    stub_readiness(monkeypatch, packet.workspace_id)
    monkeypatch.setattr(
        service,
        "read_history",
        AsyncMock(
            return_value=InvestigationPage(
                workspace_id=workspace, version_id=intent.version_id, items=(packet,)
            )
        ),
    )
    monkeypatch.setattr("accord.personas.similarity_http.authorize_actor", AsyncMock())
    monkeypatch.setattr("accord.personas.similarity_service.observation", Mock())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(workspace)), base_url="http://fixture"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/investigations"
        for route in ("generate", "readiness", "history"):
            assert (await client.post(f"{path}/{route}", json={})).status_code == 401
        headers = {"x-synthetic-session": "current"}
        response = await client.post(
            f"{path}/generate", json=intent.model_dump(mode="json"), headers=headers
        )
        assert response.status_code == 200 and "no-store" in response.headers["cache-control"]
        assert (
            response.json()["actor_ref"] == "synthetic-human" and "ciphertext" not in response.text
        )
        assert (await client.post(f"{path}/readiness", json={}, headers=headers)).json()[
            "state"
        ] == "processing_unavailable"
        assert (
            await client.post(
                f"{path}/history", json={"version_id": str(intent.version_id)}, headers=headers
            )
        ).status_code == 200
        bad = await client.post(
            f"{path}/generate",
            json={**intent.model_dump(mode="json"), "actor_ref": "browser"},
            headers=headers,
        )
        assert bad.status_code == 422 and generate.await_count == 1


def stub_readiness(monkeypatch: pytest.MonkeyPatch, workspace: UUID) -> None:
    monkeypatch.setattr(
        service,
        "readiness",
        AsyncMock(
            return_value=InvestigationReadiness(
                workspace_id=workspace,
                state="processing_unavailable",
            )
        ),
    )


@pytest.mark.asyncio
async def test_metadata_authorization_denial_and_provider_error_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, intent = uuid4(), command()
    generate = AsyncMock(side_effect=RuntimeError("sensitive provider bytes"))
    monkeypatch.setattr(service, "generate", generate)
    auth = AsyncMock(side_effect=AccessDeniedError("denied"))
    monkeypatch.setattr("accord.personas.similarity_http.authorize_actor", auth)
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    monkeypatch.setattr("accord.personas.similarity_service.observation", Mock())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(workspace)), base_url="http://fixture"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/investigations/generate"
        headers = {"x-synthetic-session": "current"}
        denied = await client.post(path, content=b"invalid", headers=headers)
        assert denied.status_code == 403 and not generate.called
        auth.side_effect = None
        unavailable = await client.post(path, json=intent.model_dump(mode="json"), headers=headers)
        assert unavailable.status_code == 503 and "sensitive" not in unavailable.text
