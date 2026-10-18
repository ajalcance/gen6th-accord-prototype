"""Narrowed app executes/replays through the actual disposable reference SQL profile."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import replace
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from personas.runtime_fixtures import config
from personas.test_job_database import setup_job
from personas.test_reference_bootstrap import platform, reference_settings
from personas.workflow_fixtures import human
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas import job_service, reference_app, runtime_role
from accord.personas.reference_bootstrap import ReferenceRuntime, build_reference
from accord.personas.task_google import TaskReference
from sql_roles.test_runtime_journeys import seed_member, workload_session


async def test_reference_factory_executes_and_replays_with_confined_sql(
    role_db: Any, role_database_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    platform(monkeypatch)
    workspace = await seed_member(role_database_url)
    value = config().model_copy(update={"workspace_id": workspace})
    settings = reference_settings(value)
    prepared = build_reference(settings)
    async with workload_session(role_database_url, role_db.roles["api"]) as api:
        intent, fixtures = await setup_job(api, workspace)
        jobs = replace(
            prepared.jobs,
            wrapper=fixtures.wrapper,
            faces=fixtures.faces,
            dispatcher=fixtures.dispatcher,
        )
        queued = await job_service.enqueue(api, workspace, human("creator-a"), intent, jobs)
    assert isinstance(jobs.dispatcher, AsyncMock)
    jobs.dispatcher.dispatch.side_effect = None
    identity = AsyncMock()
    identity.verify.return_value = value.tasks.service_email
    monkeypatch.setattr(reference_app, "get_settings", lambda: settings)
    monkeypatch.setattr(
        reference_app, "build_reference", lambda _: ReferenceRuntime(jobs, identity)
    )

    def maker() -> AbstractAsyncContextManager[AsyncSession]:
        return workload_session(role_database_url, role_db.roles["reference"])

    monkeypatch.setattr(runtime_role, "_get_sessionmaker", lambda: maker)
    app = reference_app.create_reference_app()
    app.dependency_overrides[get_db] = reference_sessions(
        role_database_url, role_db.roles["reference"]
    )
    ref = TaskReference(workspace_id=workspace, job_id=queued.job_id, dispatch_id=queued.job_id)
    async with app.router.lifespan_context(app):
        await deliver(app, ref)
    async with workload_session(role_database_url, role_db.roles["api"]) as api:
        replay = await job_service.enqueue(api, workspace, human("creator-a"), intent, jobs)
        assert replay.state == "succeeded" and replay.attempts == 1


def reference_sessions(url: str, role: str) -> Callable[[], AsyncIterator[AsyncSession]]:
    async def sessions() -> AsyncIterator[AsyncSession]:
        async with workload_session(url, role) as session:
            yield session

    return sessions


async def deliver(app: FastAPI, ref: TaskReference) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://synthetic"
    ) as client:
        headers = {"Authorization": "Bearer synthetic-verified-delivery"}
        result = await client.post("/internal/personas/jobs/reconcile", headers=headers)
        assert result.status_code == 200 and result.json() == {"examined": 1, "dispatched": 1}
        for _ in range(2):
            result = await client.post(
                "/internal/personas/jobs/execute", headers=headers, json=ref.model_dump(mode="json")
            )
            assert result.status_code == 200 and result.json() == {"state": "acknowledged"}
