"""Configuration and post-processing permission checks remain separate from activation."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from accord.config import Settings
from accord.db.connection import get_db
from accord.personas import face_service, runtime_http
from accord.personas.face_contracts import FaceCommand
from accord.personas.photo_bootstrap import photo_providers
from accord.personas.repository import AccessDeniedError
from accord.personas.runtime_bootstrap import PersonaRuntime
from personas.job_test_support import face_result
from personas.runtime_fixtures import job_rows
from personas.test_photo_http import Verifier, unbound_db
from personas.test_photo_storage import FixtureWrapper


def test_google_only_wrap_does_not_require_vault_but_partial_legacy_config_fails() -> None:
    settings = Settings(
        _env_file=None,
        persona_api_enabled=True,
        persona_photos_enabled=True,
        persona_google_enabled=True,
    )
    inspector, wrapper = photo_providers(settings)
    assert inspector is not None and wrapper is None
    with pytest.raises(ValueError):
        photo_providers(settings.model_copy(update={"photo_vault_token": SecretStr(uuid4().hex)}))
    with pytest.raises(ValueError):
        photo_providers(settings.model_copy(update={"persona_google_enabled": False}))


@pytest.mark.asyncio
async def test_membership_revoked_after_encryption_prevents_result_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, _ = job_rows()
    command = FaceCommand.model_validate(row.command)
    authorization = AsyncMock(side_effect=[None, AccessDeniedError("revoked")])
    monkeypatch.setattr(face_service, "authorize", authorization)
    photo, capture = Mock(), Mock(sha256="a" * 64, width=200, height=100)
    monkeypatch.setattr(face_service, "reference", AsyncMock(return_value=(photo, capture)))
    monkeypatch.setattr(face_service, "generation", AsyncMock(return_value=None))
    monkeypatch.setattr(face_service, "analysis_pixels", AsyncMock(return_value=b"synthetic"))
    monkeypatch.setattr(
        face_service, "run_processing", AsyncMock(return_value=(face_result(row), ()))
    )
    stored = AsyncMock()
    monkeypatch.setattr(face_service, "store_result", stored)
    async with AsyncSession() as session:
        with pytest.raises(AccessDeniedError):
            async with session.begin():
                await face_service.process_in_transaction(
                    session, row.workspace_id, row.actor_ref, command, FixtureWrapper(), Mock()
                )
    stored.assert_awaited_once()
    assert authorization.await_count == 2


@pytest.mark.asyncio
async def test_runtime_config_observation_is_private_and_does_not_probe_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = uuid4()
    member = AsyncMock()
    monkeypatch.setattr(runtime_http, "authorize_actor", member)
    monkeypatch.setattr(runtime_http, "observation", Mock())
    app = FastAPI()
    app.include_router(runtime_http.create_runtime_router(Verifier(workspace), PersonaRuntime()))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{workspace}/personas/runtime/readiness"
        assert (await client.post(path)).status_code == 401
        response = await client.post(path, headers={"x-synthetic-session": "current"})
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert response.json()["acceptance"] == "live_rehearsal_required"
        assert not response.json()["face_jobs_configured"]
        member.side_effect = AccessDeniedError("private")
        monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
        assert (
            await client.post(path, headers={"x-synthetic-session": "current"})
        ).status_code == 403
