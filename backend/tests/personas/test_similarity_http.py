"""ASGI private routing, verified identity, bounded metadata and expiry response semantics."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.repository import AccessDeniedError
from accord.personas.similarity_contracts import ClearReceipt, SearchCommand, SimilarityReadiness
from accord.personas.similarity_http import authorized_intent
from accord.personas.workflow_contracts import WorkflowActor
from personas.test_capture_http import private_app


@pytest.mark.asyncio
async def test_membership_denial_precedes_metadata_consumption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    consumed = False

    async def receive() -> dict[str, object]:
        nonlocal consumed
        consumed = True
        return {"type": "http.request", "body": b"invalid", "more_body": False}

    monkeypatch.setattr(
        "accord.personas.similarity_http.authorize_actor",
        AsyncMock(side_effect=AccessDeniedError("denied")),
    )
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    request = Request({"type": "http", "headers": []}, receive)
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            await authorized_intent(
                session,
                uuid4(),
                WorkflowActor(actor_ref="fixture", kind="human"),
                request,
                SearchCommand,
            )
    assert not consumed


@pytest.mark.asyncio
async def test_private_readiness_clear_expiry_and_invalid_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, query = uuid4(), uuid4()
    readiness = AsyncMock(
        return_value=SimilarityReadiness(
            workspace_id=workspace, state="processing_unavailable", policy_id=None
        )
    )
    clear = AsyncMock(return_value=ClearReceipt(workspace_id=workspace, query_id=query))
    search = AsyncMock(side_effect=HTTPException(410, "private-sensitive-detail"))
    monkeypatch.setattr("accord.personas.similarity_http.service.readiness", readiness)
    monkeypatch.setattr("accord.personas.similarity_http.service.clear", clear)
    monkeypatch.setattr("accord.personas.similarity_http.service.search", search)
    monkeypatch.setattr("accord.personas.similarity_http.authorize_actor", AsyncMock())
    monkeypatch.setattr("accord.personas.similarity_http.service.observation", Mock())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(workspace)), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/similarity"
        assert (await client.post(path + "/readiness")).status_code == 401
        readiness.assert_not_called()
        headers = {"x-synthetic-session": "current"}
        ok = await client.post(path + "/readiness", json={}, headers=headers)
        assert ok.status_code == 200 and ok.headers["cache-control"] == "no-store"
        assert ok.json()["state"] == "processing_unavailable"
        closed = await client.post(path + "/clear", json={"query_id": str(query)}, headers=headers)
        assert closed.status_code == 200 and closed.json()["closed"]
        command = {
            "query_id": str(query),
            "request_id": str(uuid4()),
            "face_index": 0,
            "scope": "current",
        }
        changes_list: list[dict[str, object]] = [
            {"actor_ref": "forged"},
            {"scope": "public"},
            {"threshold": 0},
            {"face_index": True},
        ]
        for changes in changes_list:
            bad = await client.post(path + "/search", json={**command, **changes}, headers=headers)
            assert bad.status_code == 422
        search.assert_not_called()
        expired = await client.post(path + "/search", json=command, headers=headers)
        assert expired.status_code == 410 and expired.headers["cache-control"] == "no-store"
        assert "private-sensitive-detail" not in expired.text


@pytest.mark.asyncio
async def test_metadata_overflow_and_thumbnail_private_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, query = uuid4(), uuid4()
    monkeypatch.setattr("accord.personas.similarity_http.authorize_actor", AsyncMock())
    monkeypatch.setattr("accord.personas.similarity_http.service.observation", Mock())
    monkeypatch.setattr(
        "accord.personas.similarity_http.service.thumbnail",
        AsyncMock(return_value=b"\x89PNG\r\n\x1a\nfixture"),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=private_app(workspace)), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/photos/similarity"
        headers = {"x-synthetic-session": "current"}
        too_large = await client.post(path + "/clear", content=b"x" * 4097, headers=headers)
        assert too_large.status_code == 422
        image = await client.get(path + f"/queries/{query}/thumbnail", headers=headers)
        assert image.status_code == 200 and "no-store" in image.headers["cache-control"]
        assert image.headers["x-content-type-options"] == "nosniff"
