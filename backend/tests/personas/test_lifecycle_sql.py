"""Disposable PostgreSQL only: ledger persistence, cross-version suspension and RLS."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import lifecycle_reads as reads
from accord.personas import lifecycle_service as lifecycle
from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.lifecycle_contracts import (
    AppendLifecycle,
    LifecycleHistory,
    Response,
    Subject,
)
from accord.personas.lifecycle_models import LifecycleRecord
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from personas.conftest import command as save_command
from personas.lifecycle_fixtures import (
    assessment,
    command,
    concern_command,
    dossier,
    response_command,
)
from personas.workflow_fixtures import human


async def prepared(session: AsyncSession, workspace: UUID) -> AppendLifecycle:
    session.add(WorkspaceMember(workspace_id=workspace, actor_ref="reviewer", role="reviewer"))
    await session.commit()
    version = await save(session, workspace, "creator-a", save_command())
    content = dossier()
    now = datetime.now(UTC)
    for key in (content.operator.evidence_id, content.rights[0].evidence_id):
        session.add(
            PrivateEvidence(
                id=key,
                workspace_id=workspace,
                version_id=version.version_id,
                owner_ref="creator-a",
                request_id=uuid4(),
                fingerprint="a" * 64,
                media_type="text/plain",
                byte_length=1,
                sha256="a" * 64,
                recorded_at=now,
                expires_at=now + timedelta(days=7),
            )
        )
        await session.flush()
        session.add_all(
            [
                EvidenceInspection(
                    evidence_id=key,
                    workspace_id=workspace,
                    verdict="clean",
                    engine="Fixture",
                    definitions="Fixture",
                    inspected_at=now,
                ),
                EvidencePayload(
                    evidence_id=key,
                    workspace_id=workspace,
                    ciphertext=b"x" * 17,
                    nonce=b"n" * 12,
                    key_id="fixture",
                    wrapped_key=b"w",
                ),
            ]
        )
    await session.commit()
    return command(version.version_id).model_copy(update={"content": content})


async def test_dossier_reviews_replay_replacement_and_durable_hashes(
    session: AsyncSession, workspace: UUID
) -> None:
    c = await prepared(session, workspace)
    profile = await lifecycle.append(session, workspace, human("creator-a"), c)
    assert await lifecycle.append(session, workspace, human("creator-a"), c) == profile
    for dimension in ("operator", "rights", "content"):
        await lifecycle.append(
            session,
            workspace,
            human("reviewer"),
            AppendLifecycle(
                version_id=c.version_id,
                request_id=uuid4(),
                content=assessment(profile.id, dimension),
            ),
        )
    result = await reads.read(session, workspace, human("viewer"), Subject(version_id=c.version_id))
    assert all(item.status == "approved" for item in result.requirements)
    assert result.requirements[0].assessment is not None
    assert result.requirements[0].assessment.evidence_digests
    replacement = await lifecycle.append(
        session,
        workspace,
        human("creator-a"),
        c.model_copy(update={"request_id": uuid4(), "expected_previous_id": profile.id}),
    )
    result = await reads.read(session, workspace, human("viewer"), Subject(version_id=c.version_id))
    assert result.dossier is not None
    assert result.dossier.id == replacement.id and all(
        item.status == "missing" for item in result.requirements
    )
    with pytest.raises(ConflictError):
        await lifecycle.append(
            session,
            workspace,
            human("reviewer"),
            AppendLifecycle(
                version_id=c.version_id, request_id=uuid4(), content=assessment(profile.id)
            ),
        )


async def test_concern_does_not_suspend_until_independent_decision_and_survives_new_version(
    session: AsyncSession, workspace: UUID
) -> None:
    c = await prepared(session, workspace)
    report = await lifecycle.append(
        session,
        workspace,
        human("viewer"),
        concern_command(c.version_id),
    )
    assert not (
        await reads.read(session, workspace, human("viewer"), Subject(version_id=c.version_id))
    ).suspended
    response = response_command(c.version_id, report.id)
    with pytest.raises(AccessDeniedError):
        await lifecycle.append(session, workspace, human("creator-a"), response)
    decision = await lifecycle.append(session, workspace, human("reviewer"), response)
    version = await save(
        session,
        workspace,
        "creator-a",
        save_command(persona_id=report.persona_id, expected_revision=1),
    )
    assert (
        await reads.read(
            session, workspace, human("viewer"), Subject(version_id=version.version_id)
        )
    ).suspended
    page = await reads.history(
        session, workspace, human("reviewer"), LifecycleHistory(version_id=version.version_id)
    )
    assert page.concerns[0].response is not None
    assert page.concerns[0].response.id == decision.id
    resolution = response.model_copy(
        update={
            "version_id": version.version_id,
            "request_id": uuid4(),
            "expected_previous_id": decision.id,
            "content": Response(
                kind="response",
                concern_id=report.id,
                decision="resolved",
                statement="Resolved synthetic case",
            ),
        }
    )
    await lifecycle.append(session, workspace, human("reviewer"), resolution)
    assert not (
        await reads.read(
            session, workspace, human("viewer"), Subject(version_id=version.version_id)
        )
    ).suspended


async def test_lifecycle_immutable_and_rls(session: AsyncSession, workspace: UUID) -> None:
    c = await prepared(session, workspace)
    await lifecycle.append(session, workspace, human("creator-a"), c)
    with pytest.raises(DBAPIError, match="immutable"):
        await session.execute(update(LifecycleRecord).values(actor_ref="viewer"))
    await session.rollback()
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
        assert (await session.scalars(select(LifecycleRecord))).all() == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :w, true)"), {"w": str(uuid4())}
        )
        assert (await session.scalars(select(LifecycleRecord))).all() == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :w, true)"), {"w": str(workspace)}
        )
        assert len((await session.scalars(select(LifecycleRecord))).all()) == 1


@pytest.mark.parametrize("requirement", [None, "unknown"])
async def test_database_rejects_assessment_without_a_valid_dimension(
    session: AsyncSession,
    workspace: UUID,
    requirement: str | None,
) -> None:
    c = await prepared(session, workspace)
    profile = await lifecycle.append(session, workspace, human("creator-a"), c)
    invalid = LifecycleRecord(
        id=uuid4(),
        workspace_id=workspace,
        persona_id=profile.persona_id,
        version_id=c.version_id,
        request_id=uuid4(),
        expected_previous_id=None,
        target_id=profile.id,
        ordinal=2,
        actor_ref="reviewer",
        kind="assessment",
        requirement=requirement,
        recorded_at=datetime.now(UTC),
        fingerprint="a" * 64,
        content=assessment(profile.id).model_dump(mode="json"),
        evidence_digests={},
    )
    session.add(invalid)
    with pytest.raises(DBAPIError, match="check constraint"):
        await session.flush()
    await session.rollback()
