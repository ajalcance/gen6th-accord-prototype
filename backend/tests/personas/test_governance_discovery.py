"""Owner/CI PostgreSQL evidence for bounded authorized discovery and rechecked membership."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.campaigns import offer_campaign
from accord.personas.evidence_service import enqueue
from accord.personas.governance_contracts import VersionHistoryQuery, VersionObjectsQuery
from accord.personas.governance_index import campaign_offers, evidence_list
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from accord.personas.version_history import version_history
from personas.campaign_fixtures import campaign_material, offer_intent
from personas.conftest import command
from personas.private_evidence_fixtures import EphemeralTestWrapper, chunks, intent
from personas.workflow_fixtures import human


async def test_versions_are_exact_persona_scoped_ordered_and_paged(
    session: AsyncSession, workspace: UUID
) -> None:
    first = await save(session, workspace, "creator-a", command())
    second = await save(
        session,
        workspace,
        "creator-a",
        command("Fictional next", persona_id=first.persona_id, expected_revision=1),
    )
    await save(session, workspace, "creator-a", command("Fictional other"))
    page = await version_history(
        session,
        workspace,
        human("viewer"),
        VersionHistoryQuery(persona_id=first.persona_id, limit=1),
    )
    older = await version_history(
        session,
        workspace,
        human("viewer"),
        VersionHistoryQuery(
            persona_id=first.persona_id, before_revision=page.next_before_revision, limit=1
        ),
    )
    assert page.items == (second,) and older.items == (first,)
    assert page.next_before_revision == 2 and older.next_before_revision is None
    events = list(
        await session.scalars(select(Event).where(Event.action == "persona.workflow_observed"))
    )
    assert len(events) == 2 and all(
        event.actor_id == "viewer" and event.source == "server" for event in events
    )


async def test_campaign_discovery_is_party_only_and_paged(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, assets = await campaign_material(session, workspace)
    offers = [
        await offer_campaign(
            session,
            workspace,
            human("creator-a"),
            offer_intent(version.version_id, review.id, assets),
        )
        for _ in range(3)
    ]
    query = VersionObjectsQuery(version_id=version.version_id, limit=2)
    page = await campaign_offers(session, workspace, human("reviewer-b"), query)
    next_page = await campaign_offers(
        session,
        workspace,
        human("reviewer-b"),
        query.model_copy(update={"after_id": page.next_after_id}),
    )
    assert [*page.items, *next_page.items] == sorted(offers, key=lambda row: row.id)
    assert page.next_after_id == page.items[-1].id and next_page.next_after_id is None
    assert not (await campaign_offers(session, workspace, human("viewer"), query)).items
    with pytest.raises(AccessDeniedError):
        await campaign_offers(session, uuid4(), human("reviewer-b"), query)


async def test_evidence_discovery_is_owner_only_even_when_empty(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    query = VersionObjectsQuery(version_id=version.version_id, limit=1)
    assert not (await evidence_list(session, workspace, human("creator-a"), query)).items
    for actor in ("creator-b", "viewer", "absent-member"):
        with pytest.raises(AccessDeniedError):
            await evidence_list(session, workspace, human(actor), query)
    records = [
        await enqueue(
            session,
            workspace,
            human("creator-a"),
            intent(version.version_id),
            chunks(),
            EphemeralTestWrapper(),
        )
        for _ in range(2)
    ]
    page = await evidence_list(session, workspace, human("creator-a"), query)
    later = await evidence_list(
        session,
        workspace,
        human("creator-a"),
        query.model_copy(update={"after_id": page.next_after_id}),
    )
    assert [*page.items, *later.items] == sorted(records, key=lambda row: row.id)
    assert all(row.state == "quarantined" for row in [*page.items, *later.items])
    assert (
        not {"ciphertext", "wrapped_key", "nonce", "key_id", "owner_ref"}
        & page.items[0].model_dump().keys()
    )


async def test_each_discovery_rechecks_membership_and_resource_scope(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    with pytest.raises(AccessDeniedError):
        await version_history(
            session, workspace, human("viewer"), VersionHistoryQuery(persona_id=uuid4())
        )
    await session.execute(
        delete(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace, WorkspaceMember.actor_ref == "viewer"
        )
    )
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await version_history(
            session,
            workspace,
            human("viewer"),
            VersionHistoryQuery(persona_id=version.persona_id),
        )
    await session.execute(
        update(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace,
            WorkspaceMember.actor_ref == "creator-a",
        )
        .values(role="viewer")
    )
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await evidence_list(
            session,
            workspace,
            human("creator-a"),
            VersionObjectsQuery(version_id=version.version_id),
        )
