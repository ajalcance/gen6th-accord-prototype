"""All human controls and configured-scope reconciliation use actual private ASGI schemas."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from accord.db.connection import get_db
from accord.personas import job_service, job_worker, passport_http
from accord.personas.job_contracts import JobPage, JobUpdate
from accord.personas.job_http import create_job_router, create_task_router
from accord.personas.job_repository import receipt
from personas.job_test_support import runtime
from personas.runtime_fixtures import job_rows
from personas.test_photo_http import Verifier, unbound_db


@pytest.mark.asyncio
async def test_history_and_update_serialize_exact_reference_and_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, event = job_rows()
    monkeypatch.setattr(passport_http, "authorize_actor", AsyncMock())
    monkeypatch.setattr(passport_http, "observation", Mock())
    page = JobPage(
        workspace_id=row.workspace_id,
        version_id=row.version_id,
        portrait_id=row.portrait_id,
        items=(receipt(row, event),),
        overflow=False,
    )
    monkeypatch.setattr(job_service, "history", AsyncMock(return_value=page))
    changed = receipt(row, event).model_copy(update={"state": "cancelled", "sequence": 1})
    update = AsyncMock(return_value=changed)
    monkeypatch.setattr(job_service, "update", update)
    app = FastAPI()
    app.include_router(create_job_router(Verifier(row.workspace_id), runtime(row)))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path, headers = f"/api/workspaces/{row.workspace_id}/personas/jobs", {
            "x-synthetic-session": "current"
        }
        result = await client.post(
            f"{path}/history",
            json={"version_id": str(row.version_id), "portrait_id": str(row.portrait_id)},
            headers=headers,
        )
        assert result.status_code == 200 and result.json()["items"][0]["job_id"] == str(row.id)
        command = JobUpdate(job_id=row.id, request_id=uuid4(), expected_sequence=0, action="cancel")
        result = await client.post(
            f"{path}/update", json=command.model_dump(mode="json"), headers=headers
        )
        assert result.status_code == 200 and result.json()["state"] == "cancelled"
        assert update.await_args is not None and update.await_args.args[3] == command
        assert (
            await client.post(
                f"{path}/update",
                json={**command.model_dump(mode="json"), "expected_sequence": True},
                headers=headers,
            )
        ).status_code == 422


@pytest.mark.asyncio
async def test_machine_reconciliation_uses_configured_scope_not_a_body_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row, _event = job_rows()
    active = runtime(row)
    identity = Mock(verify=AsyncMock(return_value="verified-workload"))
    reconcile = AsyncMock(return_value={"examined": 1, "dispatched": 1})
    monkeypatch.setattr(job_worker, "reconcile", reconcile)
    app = FastAPI()
    app.include_router(create_task_router(active, identity))
    app.dependency_overrides[get_db] = unbound_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        path = "/internal/personas/jobs/reconcile"
        assert (
            await client.post(path, headers={"x-cloudtasks-taskname": "claimed"})
        ).status_code == 401
        result = await client.post(
            path,
            json={"workspace_id": str(uuid4()), "actor_ref": "browser"},
            headers={"Authorization": "Bearer synthetic-delivery"},
        )
        assert result.status_code == 200 and result.json() == {"examined": 1, "dispatched": 1}
        assert reconcile.await_args is not None and reconcile.await_args.args[1:] == (
            active,
            "verified-workload",
        )
