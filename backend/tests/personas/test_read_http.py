"""Owner/CI PostgreSQL proof through actual ASGI routes and a synthetic session verifier."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.db.connection import get_db
from accord.personas.models import WorkspaceMember
from accord.personas.read_http import create_read_router
from accord.personas.service import save
from personas.conftest import command
from personas.test_session_boundary import verified


@asynccontextmanager
async def read_client(session: AsyncSession, provider: AsyncMock) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    app.include_router(create_read_router(provider))

    async def database() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


def viewer() -> AsyncMock:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    return provider


async def test_http_reads_gallery_and_exact_version_with_server_actor(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    provider = viewer()
    async with read_client(session, provider) as client:
        page = await client.post(f"/api/workspaces/{workspace}/personas/query", json={"limit": 1})
        loaded = await client.post(
            f"/api/workspaces/{workspace}/personas/versions/query",
            json={"persona_id": str(version.persona_id), "revision": version.revision},
        )
    assert page.status_code == loaded.status_code == 200
    assert page.json()["items"] == [version.model_dump(mode="json")]
    assert loaded.json() == version.model_dump(mode="json")
    assert page.headers["cache-control"] == loaded.headers["cache-control"] == "no-store"
    events = list(await session.scalars(select(Event).where(Event.actor_id == "viewer")))
    assert {event.action for event in events} == {
        "persona.workspace_observed",
        "persona.version_read",
    }
    assert all(event.source == "server" and event.tenant_id == workspace for event in events)
    assert provider.verify.await_count == 2


async def test_http_never_uses_actor_claim_or_discloses_another_workspace(
    session: AsyncSession, workspace: UUID
) -> None:
    await save(session, workspace, "creator-a", command())
    async with read_client(session, viewer()) as client:
        injected = await client.post(
            f"/api/workspaces/{workspace}/personas/query", json={"actor_ref": "creator-a"}
        )
        denied = await client.post(f"/api/workspaces/{uuid4()}/personas/query", json={})
    assert injected.status_code == 422 and denied.status_code == 403
    assert denied.json() == {
        "error": {"code": "access_denied", "message": "Record access is unavailable."}
    }


async def test_http_rechecks_session_and_membership_between_pages(
    session: AsyncSession, workspace: UUID
) -> None:
    await save(session, workspace, "creator-a", command())
    provider = viewer()
    async with read_client(session, provider) as client:
        path = f"/api/workspaces/{workspace}/personas/query"
        assert (await client.post(path, json={})).status_code == 200
        provider.verify.return_value = None
        assert (await client.post(path, json={})).status_code == 401
        provider.verify.return_value = verified()
        await session.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace,
                WorkspaceMember.actor_ref == "viewer",
            )
        )
        await session.commit()
        assert (await client.post(path, json={})).status_code == 403


async def test_http_load_cannot_escape_workspace_by_persona_id(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    other = uuid4()
    session.add(WorkspaceMember(workspace_id=other, actor_ref="viewer", role="viewer"))
    await session.commit()
    async with read_client(session, viewer()) as client:
        response = await client.post(
            f"/api/workspaces/{other}/personas/versions/query",
            json={"persona_id": str(version.persona_id)},
        )
    assert response.status_code == 403
    assert str(version.version_id) not in response.text
