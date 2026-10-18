"""Private evidence HTTP and concrete adapter faults, independent of live SQL/scanner."""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas.evidence_contracts import EvidenceSnapshot
from accord.personas.evidence_http import create_evidence_router
from accord.personas.evidence_inspector import DocumentInspector
from accord.personas.photo_contracts import PhotoRejectedError, PhotoUnavailableError
from accord.personas.photo_decoder import Media
from accord.personas.photo_inspector import InspectedPhoto
from accord.personas.photo_scanner import ScanReceipt
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_contracts import WorkflowActor
from personas.private_evidence_fixtures import EphemeralTestWrapper
from personas.test_photo_http import Verifier, unbound_db


class Scanner:
    async def scan(self, data: bytes) -> ScanReceipt:
        if data == b"unavailable":
            raise PhotoUnavailableError("scanner unavailable")
        if data == b"rejected":
            raise PhotoRejectedError("rejected")
        return ScanReceipt("test-only-scanner", "test-only-definitions")


class Images:
    async def inspect(self, data: bytes, media: Media) -> InspectedPhoto:
        raise PhotoRejectedError("malformed pixels")


@pytest.mark.asyncio
async def test_document_adapter_validates_text_and_never_falls_back() -> None:
    inspector = DocumentInspector(Images(), Scanner())
    result = await inspector.inspect(b"fictional contribution\n")
    assert result.detected_type == "text/plain" and result.verdict == "clean"
    assert result.sha256 == hashlib.sha256(b"fictional contribution\n").hexdigest()
    for data in (b"\x00", b"\xff", b"rejected", b"\x89PNG\r\n\x1a\ninvalid"):
        with pytest.raises(PhotoRejectedError):
            await inspector.inspect(data)
    with pytest.raises(PhotoUnavailableError):
        await inspector.inspect(b"unavailable")


@pytest.mark.asyncio
async def test_evidence_upload_binds_headers_and_denies_foreign_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, version = uuid4(), uuid4()
    app = FastAPI()
    app.include_router(create_evidence_router(Verifier(workspace), EphemeralTestWrapper()))
    app.dependency_overrides[get_db] = unbound_db
    calls: list[object] = []

    async def enqueue(*args: object) -> EvidenceSnapshot:
        calls.extend(args[:4])
        now = datetime.now(UTC)
        return EvidenceSnapshot(
            id=uuid4(),
            workspace_id=workspace,
            version_id=version,
            media_type="text/plain",
            byte_length=4,
            sha256="a" * 64,
            recorded_at=now,
            expires_at=now + timedelta(days=7),
            state="quarantined",
        )

    monkeypatch.setattr("accord.personas.evidence_http.enqueue", enqueue)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/evidence/upload/{version}"
        headers = {
            "x-synthetic-session": "current",
            "Content-Type": "text/plain",
            "X-Request-ID": str(uuid4()),
            "X-Content-SHA256": "a" * 64,
            "X-Evidence-Length": "4",
        }
        assert (await client.post(path, content=b"text", headers=headers)).status_code == 200
        assert isinstance(calls[2], WorkflowActor) and calls[2].actor_ref == "synthetic-human"
        calls.clear()
        assert (
            await client.post(
                path.replace(str(workspace), str(uuid4())), content=b"text", headers=headers
            )
        ).status_code == 401
        assert not calls
        headers["X-Evidence-Length"] = "10485761"
        response = await client.post(path, content=b"text", headers=headers)
        assert response.status_code == 422 and response.headers["cache-control"] == "no-store"
        assert not calls


@pytest.mark.asyncio
async def test_structured_evidence_intents_are_bounded_before_inspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = uuid4()
    app = FastAPI()
    app.include_router(
        create_evidence_router(
            Verifier(workspace), EphemeralTestWrapper(), DocumentInspector(Images(), Scanner())
        )
    )
    app.dependency_overrides[get_db] = unbound_db
    auth = AsyncMock()
    inspecting = AsyncMock()
    monkeypatch.setattr("accord.personas.passport_http.authorize_actor", auth)
    monkeypatch.setattr("accord.personas.passport_http.observation", Mock())
    monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
    monkeypatch.setattr("accord.personas.evidence_http.inspect_evidence", inspecting)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/evidence/inspect"
        headers = {"x-synthetic-session": "current", "Content-Type": "application/json"}
        assert (await client.post(path, content=b" " * 65537, headers=headers)).status_code == 422
        assert (
            await client.post(path, content=b'{"evidence_id":1,"evidence_id":2}', headers=headers)
        ).status_code == 422
        inspecting.assert_not_called()
        auth.side_effect = AccessDeniedError("membership lost")
        assert (await client.post(path, content=b"invalid", headers=headers)).status_code == 403
        inspecting.assert_not_called()
