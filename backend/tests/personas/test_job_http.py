"""Real private ASGI delivery boundaries, with synthetic identity and disconnected SQL."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas import job_http as api
from accord.personas import job_service, job_worker, passport_http
from accord.personas.job_contracts import JobPage
from accord.personas.job_repository import receipt
from accord.personas.repository import AccessDeniedError
from accord.personas.task_google import TaskReference
from personas.job_test_support import runtime
from personas.runtime_fixtures import job_rows
from personas.test_photo_http import Verifier, unbound_db


@pytest.mark.asyncio
async def test_human_routes_require_session_membership_and_reference_only_intents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, event = job_rows()
    member = AsyncMock()
    monkeypatch.setattr(passport_http, "authorize_actor", member)
    monkeypatch.setattr(passport_http, "observation", Mock())
    queued = AsyncMock(return_value=receipt(row, event))
    monkeypatch.setattr(job_service, "enqueue", queued)
    monkeypatch.setattr(
        job_service,
        "history",
        AsyncMock(
            return_value=JobPage(
                workspace_id=row.workspace_id,
                version_id=row.version_id,
                portrait_id=row.portrait_id,
                items=(),
                overflow=False,
            )
        ),
    )
    app = FastAPI()
    app.include_router(api.create_job_router(Verifier(row.workspace_id), runtime(row)))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = f"/api/workspaces/{row.workspace_id}/personas/jobs"
        headers = {"x-synthetic-session": "current"}
        for route in ("enqueue", "history", "update"):
            assert (await client.post(f"{path}/{route}", content=b"invalid")).status_code == 401
        response = await client.post(f"{path}/enqueue", json=row.command, headers=headers)
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert (
            await client.post(
                f"{path}/enqueue", json={**row.command, "actor_ref": "browser"}, headers=headers
            )
        ).status_code == 422
        member.side_effect = AccessDeniedError("private membership")
        monkeypatch.setattr("accord.personas.transactions.record_rejection", AsyncMock())
        assert (
            await client.post(f"{path}/enqueue", content=b"invalid", headers=headers)
        ).status_code == 403
    queued.assert_awaited_once()


@pytest.mark.asyncio
async def test_worker_auth_precedes_payload_and_task_headers_never_authorize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, _event = job_rows()
    identity = Mock(verify=AsyncMock(return_value="verified-workload"))
    execute = AsyncMock()
    monkeypatch.setattr(job_worker, "execute", execute)
    app = FastAPI()
    app.include_router(api.create_task_router(runtime(row), identity))
    app.dependency_overrides[get_db] = unbound_db
    ref = TaskReference(workspace_id=row.workspace_id, job_id=row.id, dispatch_id=row.id)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = "/internal/personas/jobs/execute"
        claimed = {"x-cloudtasks-taskname": "claimed", "x-cloudtasks-queuename": "claimed"}
        assert (await client.post(path, content=b"invalid", headers=claimed)).status_code == 401
        identity.verify.assert_not_called()
        headers = {"Authorization": "Bearer synthetic-delivery"}
        identity.verify.side_effect = PermissionError("private claim")
        assert (await client.post(path, content=b"invalid", headers=headers)).status_code == 401
        identity.verify.side_effect = None
        assert (
            await client.post(
                path, json={**ref.model_dump(mode="json"), "actor_ref": "browser"}, headers=headers
            )
        ).status_code == 422
        response = await client.post(path, json=ref.model_dump(mode="json"), headers=headers)
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert execute.await_args is not None
        assert execute.await_args.args[-1] == "verified-workload"
        execute.side_effect = RuntimeError("private provider")
        failed = await client.post(path, json=ref.model_dump(mode="json"), headers=headers)
        assert failed.status_code == 503 and "private provider" not in failed.text


@pytest.mark.asyncio
async def test_unconfigured_worker_remains_unavailable() -> None:
    app = FastAPI()
    app.include_router(api.create_task_router(None, None))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        for route in ("execute", "reconcile"):
            assert (
                await client.post(f"/internal/personas/jobs/{route}", content=b"invalid")
            ).status_code == 503
