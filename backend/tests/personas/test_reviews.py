"""Independent, immutable decisions exercised against PostgreSQL."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.models import AuditLog, Event
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.review_models import ReviewRecord
from accord.personas.reviews import record_review
from accord.personas.service import save
from accord.personas.workflow_contracts import WorkflowActor
from personas.conftest import command
from personas.workflow_fixtures import draft_for_review, human, review_intent


async def test_review_retry_and_audit_receipt(session: AsyncSession, workspace: UUID) -> None:
    version = await draft_for_review(session, workspace)
    intent = review_intent(version.version_id)
    first = await record_review(session, workspace, human("reviewer-a"), intent)
    assert await record_review(session, workspace, human("reviewer-a"), intent) == first
    assert first.version_id == version.version_id and first.ordinal == 1
    assert await session.scalar(select(func.count()).select_from(ReviewRecord)) == 1
    event = await session.scalar(select(Event).where(Event.event_id == first.event_id))
    assert event is not None and event.actor_id == "reviewer-a" and event.source == "server"
    assert event.correlation_id == str(intent.request_id)
    assert event.metadata_ == {"version_id": str(version.version_id)}
    await session.rollback()
    assert await seal_new(session) == 2
    assert await verify_chain(session) == (True, None, 2)
    assert all(row.compliance_tags for row in (await session.scalars(select(AuditLog))).all())


async def test_append_change_request_requires_current_decision(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    first = await record_review(
        session, workspace, human("reviewer-a"), review_intent(version.version_id)
    )
    second = await record_review(
        session,
        workspace,
        human("reviewer-b"),
        review_intent(
            version.version_id,
            expected_previous_id=first.id,
            decision="changes_requested",
        ),
    )
    assert second.ordinal == 2 and second.decision == "changes_requested"
    with pytest.raises(ConflictError, match="decision changed"):
        await record_review(
            session, workspace, human("reviewer-a"), review_intent(version.version_id)
        )
    rows = list(await session.scalars(select(ReviewRecord).order_by(ReviewRecord.ordinal)))
    assert [row.decision for row in rows] == ["approved", "changes_requested"]


@pytest.mark.parametrize("actor", ["creator-a", "creator-b", "viewer", "absent-member"])
async def test_review_requires_stored_reviewer_role(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    version = await draft_for_review(session, workspace)
    with pytest.raises(AccessDeniedError):
        await record_review(session, workspace, human(actor), review_intent(version.version_id))
    assert await session.scalar(select(func.count()).select_from(ReviewRecord)) == 0


@pytest.mark.parametrize("kind", ["agent", "service"])
async def test_nonhuman_context_cannot_review(
    session: AsyncSession, workspace: UUID, kind: str
) -> None:
    version = await draft_for_review(session, workspace)
    actor = WorkflowActor.model_validate({"actor_ref": "reviewer-a", "kind": kind})
    with pytest.raises(AccessDeniedError, match="human"):
        await record_review(session, workspace, actor, review_intent(version.version_id))


async def test_role_change_cannot_enable_self_review(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    await session.execute(
        update(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace,
            WorkspaceMember.actor_ref == "creator-a",
        )
        .values(role="reviewer")
    )
    await session.commit()
    with pytest.raises(AccessDeniedError, match="self-review"):
        await record_review(
            session, workspace, human("creator-a"), review_intent(version.version_id)
        )


async def test_changed_retry_and_revoked_reviewer_denied(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    intent = review_intent(version.version_id)
    await record_review(session, workspace, human("reviewer-a"), intent)
    with pytest.raises(ConflictError, match="different content"):
        await record_review(
            session,
            workspace,
            human("reviewer-a"),
            review_intent(
                version.version_id,
                request_id=intent.request_id,
                statement="Different fixture decision.",
            ),
        )
    await session.execute(
        update(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace,
            WorkspaceMember.actor_ref == "reviewer-a",
        )
        .values(role="viewer")
    )
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await record_review(session, workspace, human("reviewer-a"), intent)


async def test_edit_blocks_new_review_but_retry_returns_historical_receipt(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    intent = review_intent(version.version_id)
    receipt = await record_review(session, workspace, human("reviewer-a"), intent)
    await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=version.persona_id,
            expected_revision=1,
        ),
    )
    with pytest.raises(ConflictError, match="no longer current"):
        await record_review(
            session, workspace, human("reviewer-b"), review_intent(version.version_id)
        )
    assert await record_review(session, workspace, human("reviewer-a"), intent) == receipt


async def test_cross_workspace_version_is_not_disclosed(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    other = uuid4()
    session.add(WorkspaceMember(workspace_id=other, actor_ref="reviewer-a", role="reviewer"))
    await session.commit()
    with pytest.raises(AccessDeniedError, match="version access"):
        await record_review(session, other, human("reviewer-a"), review_intent(version.version_id))
