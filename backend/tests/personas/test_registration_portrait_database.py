"""Owner/CI SQL proof: an initial HTTP registration binds a durable inspected portrait."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.models import Version
from accord.personas.photo_contracts import PhotoChange
from accord.personas.photo_models import VersionPortrait
from personas.conftest import command
from personas.test_photo_storage import FixtureWrapper, staged
from personas.write_http_fixtures import write_client


async def test_new_registration_binds_inspected_portrait_and_exact_replay(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    _, portrait = await staged(session, workspace, FixtureWrapper())
    intent = command(photo=PhotoChange(action="attach", upload_id=portrait)).model_dump(mode="json")
    async with write_client(session) as (client, _provider):
        path = f"/api/workspaces/{workspace}/personas/versions/save"
        response = await client.post(path, json=intent)
        assert response.status_code == 200
        replay = await client.post(path, json=intent)
        assert replay.status_code == 200 and replay.json() == response.json()
    binding = await session.get(VersionPortrait, UUID(response.json()["version_id"]))
    assert binding is not None and binding.portrait_id == portrait
    assert binding.workspace_id == workspace
    assert await session.scalar(select(func.count()).select_from(Version)) == 1


@pytest.mark.parametrize("missing", [True, False])
async def test_uninspected_or_another_owner_portrait_cannot_register(
    session: AsyncSession,
    workspace: UUID,
    missing: bool,
) -> None:
    if missing:
        portrait = uuid4()
    else:
        _, portrait = await staged(session, workspace, FixtureWrapper(), "creator-b")
    intent = command(photo=PhotoChange(action="attach", upload_id=portrait)).model_dump(mode="json")
    async with write_client(session) as (client, _provider):
        result = await client.post(
            f"/api/workspaces/{workspace}/personas/versions/save", json=intent
        )
    assert result.status_code == 403
    assert await session.scalar(select(func.count()).select_from(Version)) == 0
    assert await session.scalar(select(func.count()).select_from(VersionPortrait)) == 0
