"""Separate immutable provenance from expiring payloads; a hold never means delete."""

from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_models import EvidencePayload, PrivateEvidence
from accord.personas.evidence_service import enqueue, new_evidence, purge_expired, read_evidence
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from personas.conftest import command
from personas.private_evidence_fixtures import DATA, EphemeralTestWrapper, chunks, intent
from personas.workflow_fixtures import human


class FixtureRetention:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    async def may_purge(self, workspace_id: UUID, evidence_id: UUID) -> bool:
        return self.allowed


async def expired_evidence(session: AsyncSession, workspace: UUID) -> PrivateEvidence:
    version = await save(session, workspace, "creator-a", command())
    row, payload = await new_evidence(
        workspace, human("creator-a"), intent(version.version_id), DATA, EphemeralTestWrapper()
    )
    row.recorded_at -= timedelta(days=8)
    row.expires_at -= timedelta(days=8)
    session.add(row)
    await session.flush()
    session.add(payload)
    await session.commit()
    return row


async def test_expired_access_and_hold_denial_then_payload_only_purge(
    session: AsyncSession, workspace: UUID
) -> None:
    row = await expired_evidence(session, workspace)
    evidence_id = row.id
    actor = human("creator-a")
    with pytest.raises(AccessDeniedError):
        await read_evidence(session, workspace, actor, evidence_id, EphemeralTestWrapper())
    with pytest.raises(AccessDeniedError, match="retention"):
        await purge_expired(session, workspace, actor, evidence_id, FixtureRetention(False))
    assert await session.get(EvidencePayload, evidence_id) is not None
    await session.rollback()
    result = await purge_expired(session, workspace, actor, evidence_id, FixtureRetention(True))
    assert result.state == "expired"
    assert await session.get(EvidencePayload, evidence_id) is None
    assert await session.get(PrivateEvidence, evidence_id) is not None


async def test_unavailable_retention_gate_does_not_delete(
    session: AsyncSession, workspace: UUID
) -> None:
    class UnavailableRetention(FixtureRetention):
        async def may_purge(self, workspace_id: UUID, evidence_id: UUID) -> bool:
            raise ConnectionError("hold service unavailable")

    row = await expired_evidence(session, workspace)
    evidence_id = row.id
    with pytest.raises(ConnectionError):
        await purge_expired(
            session, workspace, human("creator-a"), evidence_id, UnavailableRetention(True)
        )
    assert await session.get(EvidencePayload, evidence_id) is not None


@pytest.mark.parametrize("operation", ["metadata", "payload", "early_delete"])
async def test_database_rejects_mutation_and_premature_deletion(
    session: AsyncSession, workspace: UUID, operation: str
) -> None:
    version = await save(session, workspace, "creator-a", command())
    receipt = await enqueue(
        session,
        workspace,
        human("creator-a"),
        intent(version.version_id),
        chunks(),
        EphemeralTestWrapper(),
    )
    with pytest.raises(DBAPIError, match="immutable|not expired"):
        if operation == "metadata":
            await session.execute(
                update(PrivateEvidence)
                .where(PrivateEvidence.id == receipt.id)
                .values(sha256="c" * 64)
            )
        elif operation == "payload":
            await session.execute(
                update(EvidencePayload)
                .where(EvidencePayload.evidence_id == receipt.id)
                .values(ciphertext=b"altered")
            )
        else:
            await session.execute(
                delete(EvidencePayload).where(EvidencePayload.evidence_id == receipt.id)
            )
    await session.rollback()


async def test_payload_rls_hides_missing_and_other_tenant_context(
    session: AsyncSession, workspace: UUID
) -> None:
    row = await expired_evidence(session, workspace)
    evidence_id = row.id
    await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
    assert (
        await session.scalar(
            select(EvidencePayload).where(EvidencePayload.evidence_id == evidence_id)
        )
        is None
    )
    await session.execute(
        text("SELECT set_config('accord.workspace_id', :scope, true)"), {"scope": str(workspace)}
    )
    assert (
        await session.scalar(
            select(EvidencePayload).where(EvidencePayload.evidence_id == evidence_id)
        )
        is not None
    )
