"""Test-only actual ASGI serialization; synthetic sessions/services, no listener or providers."""

import asyncio
import json
import sys
from contextlib import ExitStack
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.face_contracts import FaceCommand
from accord.personas.job_contracts import JobPage
from accord.personas.job_http import create_job_router
from accord.personas.job_repository import receipt
from accord.personas.runtime_bootstrap import PersonaRuntime
from accord.personas.runtime_http import create_runtime_router
from personas.job_test_support import runtime
from personas.runtime_fixtures import job_rows
from personas.test_session_boundary import verified


async def bridge(workspace: UUID, path: str, body: dict[str, Any], mode: str) -> dict[str, Any]:
    row, event = job_rows()
    row.workspace_id = workspace
    event.workspace_id = workspace
    verifier = AsyncMock()
    verifier.verify.return_value = (
        None if mode == "session_lost" else verified(actor_ref="creator-a")
    )
    app = FastAPI()
    app.include_router(create_job_router(verifier, runtime(row)))
    app.include_router(create_runtime_router(verifier, PersonaRuntime(jobs=runtime(row))))

    async def database() -> AsyncSession:
        return AsyncSession()

    async def enqueue(
        _session: AsyncSession,
        _workspace: UUID,
        _actor: object,
        command: FaceCommand,
        _runtime: object,
    ) -> object:
        row.id = row.request_id = command.request_id
        row.version_id, row.portrait_id = command.version_id, command.portrait_id
        row.command = command.model_dump(mode="json")
        return receipt(row, event)

    history = JobPage(
        workspace_id=workspace,
        version_id=body.get("version_id", row.version_id),
        portrait_id=body.get("portrait_id", row.portrait_id),
        items=(),
        overflow=False,
    )
    app.dependency_overrides[get_db] = database
    with ExitStack() as stack:
        for module in ("passport_http", "runtime_http"):
            stack.enter_context(patch(f"accord.personas.{module}.authorize_actor", AsyncMock()))
            stack.enter_context(patch(f"accord.personas.{module}.observation", Mock()))
        stack.enter_context(patch("accord.personas.job_service.enqueue", enqueue))
        stack.enter_context(
            patch("accord.personas.job_service.history", AsyncMock(return_value=history))
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://synthetic"
        ) as client:
            result = await client.post(path, json=body)
    return {"status": result.status_code, "headers": dict(result.headers), "body": result.json()}


async def main() -> None:
    command = json.loads(sys.stdin.read())
    workspace = UUID(command["workspace"])
    path = f"/api/workspaces/{workspace}/personas{command['path']}"
    print(json.dumps(await bridge(workspace, path, command["body"], command.get("mode", "ready"))))


if __name__ == "__main__":
    asyncio.run(main())
