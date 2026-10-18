"""Promotion denial, stale bindings and identity isolation at the service boundary."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_contracts import Inspection
from accord.personas.evidence_models import EvidenceInspection, PrivateEvidence
from accord.personas.evidence_service import enqueue, inspect_evidence, read_evidence
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


@pytest.mark.parametrize(
    "changes",
    [
        {"sha256": "a" * 64},
        {"byte_length": 1},
        {"detected_type": "image/png"},
        {"inspected_at": datetime.now(UTC) + timedelta(days=1)},
    ],
)
async def test_inspection_must_match_stored_bytes(
    session: AsyncSession, workspace: UUID, changes: dict[str, object]
) -> None:
    class MismatchedInspector(FixtureContentInspector):
        async def inspect(self, data: bytes) -> Inspection:
            result = await super().inspect(data)
            return Inspection.model_validate({**result.model_dump(), **changes})

    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    receipt = await enqueue(
        session, workspace, actor, intent(version.version_id), chunks(), wrapper
    )
    with pytest.raises(ValueError, match="inspection"):
        await inspect_evidence(
            session, workspace, actor, receipt.id, wrapper, MismatchedInspector()
        )
    assert await session.scalar(select(func.count()).select_from(EvidenceInspection)) == 0


async def test_rejected_inspection_never_allows_read(
    session: AsyncSession, workspace: UUID
) -> None:
    class RejectedInspector(FixtureContentInspector):
        async def inspect(self, data: bytes) -> Inspection:
            result = await super().inspect(data)
            return Inspection.model_validate({**result.model_dump(), "verdict": "rejected"})

    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    receipt = await enqueue(
        session, workspace, actor, intent(version.version_id), chunks(), wrapper
    )
    result = await inspect_evidence(
        session, workspace, actor, receipt.id, wrapper, RejectedInspector()
    )
    assert result.state == "rejected"
    with pytest.raises(AccessDeniedError):
        await read_evidence(session, workspace, actor, receipt.id, wrapper)
    repeated = await inspect_evidence(
        session, workspace, actor, receipt.id, wrapper, FixtureContentInspector()
    )
    assert repeated.state == "rejected"


async def test_new_upload_requires_current_version_but_exact_retry_is_historical(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    wrapper, actor = EphemeralTestWrapper(), human("creator-a")
    upload = intent(version.version_id)
    receipt = await enqueue(session, workspace, actor, upload, chunks(), wrapper)
    await save(
        session, workspace, "creator-a", command(persona_id=version.persona_id, expected_revision=1)
    )
    with pytest.raises(ConflictError):
        await enqueue(session, workspace, actor, intent(version.version_id), chunks(), wrapper)
    assert await enqueue(session, workspace, actor, upload, chunks(), wrapper) == receipt


async def test_cross_workspace_denied_before_consuming_stream(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await save(session, workspace, "creator-a", command())
    stream = chunks()
    with pytest.raises(AccessDeniedError):
        await enqueue(
            session,
            uuid4(),
            human("creator-a"),
            intent(version.version_id),
            stream,
            EphemeralTestWrapper(),
        )
    assert await anext(stream)
    await stream.aclose()
    assert await session.scalar(select(func.count()).select_from(PrivateEvidence)) == 0
