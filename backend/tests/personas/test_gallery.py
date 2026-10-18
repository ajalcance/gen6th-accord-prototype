"""Scoped current-head listing, literal search, pagination and durable observation."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.gallery import GalleryQuery, list_gallery
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from personas.conftest import command
from personas.workflow_fixtures import human


async def test_gallery_paginates_current_heads_once(session: AsyncSession, workspace: UUID) -> None:
    versions = [
        await save(session, workspace, "creator-a", command(f"Fictional {i}")) for i in range(3)
    ]
    changed = await save(
        session,
        workspace,
        "creator-a",
        command(
            "Fictional updated",
            persona_id=versions[0].persona_id,
            expected_revision=1,
        ),
    )
    expected = sorted([changed, *versions[1:]], key=lambda item: item.persona_id)
    first = await list_gallery(session, workspace, human("viewer"), GalleryQuery(limit=2))
    second = await list_gallery(
        session,
        workspace,
        human("viewer"),
        GalleryQuery(
            limit=2,
            after_persona_id=first.next_after_persona_id,
        ),
    )
    assert [*first.items, *second.items] == expected
    assert first.next_after_persona_id == first.items[-1].persona_id
    assert second.next_after_persona_id is None
    assert len({item.persona_id for item in [*first.items, *second.items]}) == 3


async def test_gallery_empty_results_are_observed_without_search_text(
    session: AsyncSession, workspace: UUID
) -> None:
    result = await list_gallery(
        session, workspace, human("viewer"), GalleryQuery(search="private query")
    )
    assert result.items == () and result.workspace_id == workspace
    event = (await session.scalars(select(Event))).one()
    assert event.action == "persona.workspace_observed" and event.source == "server"
    assert event.metadata_ == {"operation": "gallery_list", "returned": 0}
    assert "private query" not in str(event.metadata_)


async def test_search_escapes_wildcards_and_uses_current_name(
    session: AsyncSession, workspace: UUID
) -> None:
    exact = await save(session, workspace, "creator-a", command("Fictional 100%_Original"))
    await save(session, workspace, "creator-a", command("Fictional 100XXOriginal"))
    result = await list_gallery(
        session, workspace, human("viewer"), GalleryQuery(search="100%_original")
    )
    assert result.items == (exact,)
    await save(
        session,
        workspace,
        "creator-a",
        command("Fictional renamed", persona_id=exact.persona_id, expected_revision=1),
    )
    assert not (
        await list_gallery(
            session, workspace, human("viewer"), GalleryQuery(search="100%_original")
        )
    ).items


async def test_gallery_never_leaks_other_workspaces(session: AsyncSession, workspace: UUID) -> None:
    await save(session, workspace, "creator-a", command())
    other = uuid4()
    session.add(WorkspaceMember(workspace_id=other, actor_ref="viewer", role="viewer"))
    await session.commit()
    assert not (await list_gallery(session, other, human("viewer"), GalleryQuery())).items
    with pytest.raises(AccessDeniedError):
        await list_gallery(session, uuid4(), human("viewer"), GalleryQuery())


async def test_gallery_rechecks_removed_membership(session: AsyncSession, workspace: UUID) -> None:
    await save(session, workspace, "creator-a", command())
    await list_gallery(session, workspace, human("viewer"), GalleryQuery())
    await session.execute(
        update(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace, WorkspaceMember.actor_ref == "viewer")
        .values(actor_ref="replacement")
    )
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await list_gallery(session, workspace, human("viewer"), GalleryQuery())
