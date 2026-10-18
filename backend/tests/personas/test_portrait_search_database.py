"""Real PostgreSQL authorization, historical grouping and transient-query guarantees."""

import base64
import hashlib
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.capture_contracts import ReferenceChange
from accord.personas.models import WorkspaceMember
from accord.personas.photo_contracts import PhotoChange
from accord.personas.photo_models import Portrait, PortraitPayload
from accord.personas.portrait_search import search_portraits
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from accord.personas.workflow_contracts import WorkflowActor
from personas.conftest import command
from personas.test_photo_storage import FixtureWrapper, body, staged, upload


@pytest.mark.asyncio
@pytest.mark.parametrize("keep_references", [True, False])
async def test_search_groups_history_excludes_stages_and_never_enrolls_query(
    session: AsyncSession, workspace: UUID, keep_references: bool
) -> None:
    value, portrait = await staged(session, workspace, FixtureWrapper())
    first = await save(
        session,
        workspace,
        "creator-a",
        command(
            photo=PhotoChange(action="attach", upload_id=portrait),
        ),
    )
    kept = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=first.persona_id,
            expected_revision=1,
        ),
    )
    removed = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=first.persona_id,
            expected_revision=2,
            photo=PhotoChange(action="remove"),
            references=ReferenceChange(action="keep" if keep_references else "replace"),
        ),
    )
    await staged(session, workspace, FixtureWrapper())  # unbound matching portrait
    result = await search_portraits(
        session, workspace, WorkflowActor(actor_ref="viewer", kind="human"), body(value)
    )
    expected = removed.version_id if keep_references else kept.version_id
    assert [item.version_id for item in result.items] == [expected]
    assert result.request_id == value.request_id and result.sha256 == value.sha256
    assert not result.has_more
    assert await session.scalar(select(func.count()).select_from(Portrait)) == 2
    assert await session.scalar(select(func.count()).select_from(PortraitPayload)) == 4
    event = await session.scalar(
        select(Event).where(Event.resource_type == "persona_portrait_search")
    )
    assert event is not None and event.actor_id == "viewer" and event.metadata_["returned"] == 1


@pytest.mark.asyncio
async def test_search_cannot_disclose_another_workspace_with_identical_bytes(
    session: AsyncSession, workspace: UUID
) -> None:
    value, portrait = await staged(session, workspace, FixtureWrapper())
    await save(
        session,
        workspace,
        "creator-a",
        command(photo=PhotoChange(action="attach", upload_id=portrait)),
    )
    other = uuid4()
    session.add(WorkspaceMember(workspace_id=other, actor_ref="viewer", role="viewer"))
    await session.commit()
    actor = WorkflowActor(actor_ref="viewer", kind="human")
    assert not (await search_portraits(session, other, actor, body(value))).items
    await session.rollback()
    consumed = False

    async def unread() -> AsyncIterator[bytes]:
        nonlocal consumed
        consumed = True
        yield upload().model_dump_json().encode()

    with pytest.raises(AccessDeniedError):
        await search_portraits(session, uuid4(), actor, unread())
    assert not consumed


@pytest.mark.asyncio
async def test_search_bounds_many_matching_personas_and_returns_newest_matching_version(
    session: AsyncSession, workspace: UUID
) -> None:
    value, portrait = await staged(session, workspace, FixtureWrapper())
    for index in range(21):
        await save(
            session,
            workspace,
            "creator-a",
            command(
                name=f"Synthetic persona {index}",
                photo=PhotoChange(action="attach", upload_id=portrait),
            ),
        )
    result = await search_portraits(
        session, workspace, WorkflowActor(actor_ref="viewer", kind="human"), body(value)
    )
    assert len(result.items) == 20 and result.has_more
    ids = [item.persona_id for item in result.items]
    assert ids == sorted(set(ids))


@pytest.mark.asyncio
async def test_changed_file_bytes_do_not_become_a_performer_match(
    session: AsyncSession, workspace: UUID
) -> None:
    value, portrait = await staged(session, workspace, FixtureWrapper())
    await save(
        session,
        workspace,
        "creator-a",
        command(
            photo=PhotoChange(action="attach", upload_id=portrait),
        ),
    )
    changed = base64.b64decode(value.data) + b"synthetic trailing data"
    query = value.model_copy(
        update={
            "request_id": uuid4(),
            "data": base64.b64encode(changed).decode(),
            "byte_length": len(changed),
            "sha256": hashlib.sha256(changed).hexdigest(),
        }
    )
    result = await search_portraits(
        session, workspace, WorkflowActor(actor_ref="viewer", kind="human"), body(query)
    )
    assert not result.items and not result.has_more
    assert await session.scalar(select(func.count()).select_from(Portrait)) == 1
