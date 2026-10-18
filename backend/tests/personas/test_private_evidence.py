"""PostgreSQL private evidence tests. Run by owner/CI with a throwaway database."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.models import Event
from accord.personas.evidence_contracts import Inspection
from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.evidence_service import enqueue, inspect_evidence, read_evidence
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from personas.conftest import command
from personas.private_evidence_fixtures import (
    DATA,
    EphemeralTestWrapper,
    FixtureContentInspector,
    chunks,
    intent,
)
from personas.workflow_fixtures import human


async def test_quarantine_inspect_read_and_audit(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    upload = intent(version.version_id)
    receipt = await enqueue(session, workspace, actor, upload, chunks(), wrapper)
    assert receipt.state == "quarantined"
    assert await enqueue(session, workspace, actor, upload, chunks(), wrapper) == receipt
    with pytest.raises(AccessDeniedError):
        await read_evidence(session, workspace, actor, receipt.id, wrapper)
    clean = await inspect_evidence(
        session, workspace, actor, receipt.id, wrapper, FixtureContentInspector()
    )
    assert clean.state == "clean"
    assert await read_evidence(session, workspace, actor, receipt.id, wrapper) == DATA
    assert await session.scalar(select(func.count()).select_from(PrivateEvidence)) == 1
    assert await session.scalar(select(func.count()).select_from(EvidenceInspection)) == 1
    stored = (await session.scalars(select(EvidencePayload))).one()
    assert DATA not in stored.ciphertext
    events = list(await session.scalars(select(Event)))
    assert all(DATA.decode() not in str(event.metadata_) for event in events)
    await session.rollback()
    sealed = await seal_new(session)
    assert sealed == len(events)
    assert await verify_chain(session) == (True, None, sealed)


@pytest.mark.parametrize("actor_ref", ["creator-b", "viewer", "absent-member"])
async def test_nonowner_cannot_upload_or_read(
    session: AsyncSession, workspace: UUID, actor_ref: str
) -> None:
    version = await save(session, workspace, "creator-a", command())
    wrapper = EphemeralTestWrapper()
    upload = intent(version.version_id)
    actor = human(actor_ref)
    with pytest.raises(AccessDeniedError):
        await enqueue(session, workspace, actor, upload, chunks(), wrapper)
    with pytest.raises(AccessDeniedError):
        await read_evidence(session, workspace, actor, uuid4(), wrapper)
    assert await session.scalar(select(func.count()).select_from(PrivateEvidence)) == 0


async def test_scanner_failure_leaves_quarantine(session: AsyncSession, workspace: UUID) -> None:
    class BrokenInspector(FixtureContentInspector):
        async def inspect(self, data: bytes) -> Inspection:
            raise ConnectionError("scanner unavailable")

    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    receipt = await enqueue(
        session, workspace, actor, intent(version.version_id), chunks(), wrapper
    )
    with pytest.raises(ConnectionError):
        await inspect_evidence(session, workspace, actor, receipt.id, wrapper, BrokenInspector())
    assert await session.scalar(select(func.count()).select_from(EvidenceInspection)) == 0
    await session.rollback()
    with pytest.raises(AccessDeniedError):
        await read_evidence(session, workspace, actor, receipt.id, wrapper)


async def test_changed_retry_and_revoked_membership(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    upload = intent(version.version_id)
    receipt = await enqueue(session, workspace, actor, upload, chunks(), wrapper)
    changed = intent(version.version_id, b"changed", request_id=upload.request_id)
    with pytest.raises(ConflictError):
        await enqueue(session, workspace, actor, changed, chunks(b"changed"), wrapper)
    await session.execute(
        update(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace, WorkspaceMember.actor_ref == actor.actor_ref
        )
        .values(role="viewer")
    )
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await enqueue(session, workspace, actor, upload, chunks(), wrapper)
    with pytest.raises(AccessDeniedError):
        await inspect_evidence(
            session, workspace, actor, receipt.id, wrapper, FixtureContentInspector()
        )


async def test_intake_failure_rolls_back_everything(session: AsyncSession, workspace: UUID) -> None:
    version = await save(session, workspace, "creator-a", command())
    with pytest.raises(ValueError):
        await enqueue(
            session,
            workspace,
            human("creator-a"),
            intent(version.version_id),
            chunks(b"incorrect bytes"),
            EphemeralTestWrapper(),
        )
    assert await session.scalar(select(func.count()).select_from(PrivateEvidence)) == 0
    assert await session.scalar(select(func.count()).select_from(EvidencePayload)) == 0
