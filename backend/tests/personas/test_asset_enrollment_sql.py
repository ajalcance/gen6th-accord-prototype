"""Actual SQL persistence/immutability proof, executed only on disposable owner/CI PostgreSQL."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.asset_contracts import EnrollAsset
from accord.personas.asset_models import AssetEnrollment
from accord.personas.asset_service import enroll
from accord.personas.campaign_models import PersonaAsset
from accord.personas.evidence_service import enqueue, inspect_evidence
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from personas.conftest import command
from personas.private_evidence_fixtures import (
    EphemeralTestWrapper,
    FixtureContentInspector,
    chunks,
    intent,
)
from personas.workflow_fixtures import human


@pytest.mark.asyncio
async def test_clean_evidence_requires_explicit_enrollment_and_is_immutable(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    evidence = await enqueue(
        session, workspace, actor, intent(version.version_id), chunks(), wrapper
    )
    enrollment = EnrollAsset(
        request_id=uuid4(),
        version_id=version.version_id,
        evidence_id=evidence.id,
        label="Fictional production asset",
        permission_statement="Fixture creator grants consideration only.",
    )
    with pytest.raises(AccessDeniedError):
        await enroll(session, workspace, actor, enrollment)
    scanned = await inspect_evidence(
        session, workspace, actor, evidence.id, wrapper, FixtureContentInspector()
    )
    registered = await enroll(session, workspace, actor, enrollment)
    assert registered.asset.digest == scanned.sha256
    assert await enroll(session, workspace, actor, enrollment) == registered
    with pytest.raises(ConflictError):
        await enroll(
            session, workspace, actor, enrollment.model_copy(update={"request_id": uuid4()})
        )
    with pytest.raises(DBAPIError):
        await session.execute(
            update(AssetEnrollment)
            .where(AssetEnrollment.asset_id == registered.asset.id)
            .values(permission_statement="altered")
        )
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize("actor", ["creator-b", "viewer"])
async def test_foreign_owner_and_viewer_cannot_enroll_private_bytes(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    version = await save(session, workspace, "creator-a", command())
    evidence = await enqueue(
        session,
        workspace,
        human("creator-a"),
        intent(version.version_id),
        chunks(),
        EphemeralTestWrapper(),
    )
    with pytest.raises(AccessDeniedError):
        await enroll(
            session,
            workspace,
            human(actor),
            EnrollAsset(
                request_id=uuid4(),
                version_id=version.version_id,
                evidence_id=evidence.id,
                label="Attempt",
                permission_statement="Unauthorized attempt.",
            ),
        )
    assert await session.scalar(select(AssetEnrollment.asset_id)) is None


async def test_database_rejects_evidence_bound_to_a_different_version(
    session: AsyncSession, workspace: UUID
) -> None:
    original = await save(session, workspace, "creator-a", command())
    evidence = await enqueue(
        session,
        workspace,
        human("creator-a"),
        intent(original.version_id),
        chunks(),
        EphemeralTestWrapper(),
    )
    other = await save(session, workspace, "creator-a", command("Different fictional persona"))
    asset = uuid4()
    session.add(
        PersonaAsset(
            id=asset,
            workspace_id=workspace,
            version_id=other.version_id,
            digest=evidence.sha256,
            label="Other version",
        )
    )
    await session.commit()
    with pytest.raises(DBAPIError, match="foreign key"):
        async with session.begin():
            session.add(
                AssetEnrollment(
                    asset_id=asset,
                    workspace_id=workspace,
                    version_id=other.version_id,
                    evidence_id=evidence.id,
                    owner_ref="creator-a",
                    request_id=uuid4(),
                    fingerprint="a" * 64,
                    permission_statement="Deliberate binding fault.",
                    recorded_at=datetime.now(UTC),
                )
            )
