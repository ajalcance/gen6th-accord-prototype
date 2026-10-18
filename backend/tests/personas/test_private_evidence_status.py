"""Metadata status stays private and never needs a key provider or returns secret material."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.evidence_service import enqueue, inspect_evidence
from accord.personas.evidence_status import evidence_status
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from personas.conftest import command
from personas.private_evidence_fixtures import (
    EphemeralTestWrapper,
    FixtureContentInspector,
    chunks,
    intent,
)
from personas.workflow_fixtures import human


async def test_owner_status_observes_quarantine_then_clean_without_private_material(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    actor, wrapper = human("creator-a"), EphemeralTestWrapper()
    queued = await enqueue(session, workspace, actor, intent(version.version_id), chunks(), wrapper)
    assert (await evidence_status(session, workspace, actor, queued.id)).state == "quarantined"
    await inspect_evidence(session, workspace, actor, queued.id, wrapper, FixtureContentInspector())
    result = await evidence_status(session, workspace, actor, queued.id)
    assert result.state == "clean"
    assert (
        not {"ciphertext", "wrapped_key", "key_id", "nonce", "owner_ref"}
        & result.model_dump().keys()
    )
    events = list(
        await session.scalars(select(Event).where(Event.action == "persona.evidence_read"))
    )
    assert len(events) == 2
    assert all(
        event.metadata_["view"] == "metadata" and event.source == "server" for event in events
    )


@pytest.mark.parametrize("actor", ["creator-b", "viewer", "absent-member"])
async def test_private_status_requires_current_owner_membership(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    version = await save(session, workspace, "creator-a", command())
    queued = await enqueue(
        session,
        workspace,
        human("creator-a"),
        intent(version.version_id),
        chunks(),
        EphemeralTestWrapper(),
    )
    with pytest.raises(AccessDeniedError):
        await evidence_status(session, workspace, human(actor), queued.id)
