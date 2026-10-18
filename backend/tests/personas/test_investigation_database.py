"""Owner/CI PostgreSQL lane; collection does not prove SQL execution or live Gemini."""

from dataclasses import replace
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.investigation_contracts import InvestigationCommand, InvestigationHistory
from accord.personas.investigation_models import InvestigationRecord
from accord.personas.investigation_provider import ComparisonOutput, InvestigationRuntime
from accord.personas.investigation_review_contracts import InvestigationReviewCommand
from accord.personas.investigation_review_models import InvestigationReviewRequest
from accord.personas.investigation_reviews import history as request_history
from accord.personas.investigation_reviews import request_review
from accord.personas.investigation_service import generate, read_history
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.similarity_service import clear, search
from accord.personas.workflow_contracts import WorkflowActor
from personas.investigation_fixtures import result
from personas.test_similarity_database import enrolled, setup_query


async def setup(
    session: AsyncSession, workspace: UUID
) -> tuple[InvestigationRuntime, InvestigationCommand]:
    similarity, query = await setup_query(workspace)
    await enrolled(session, workspace, similarity)
    page = await search(
        session, workspace, WorkflowActor(actor_ref="viewer", kind="human"), query, similarity
    )
    c = page.items[0]
    command = InvestigationCommand(
        **query.model_dump(),
        version_id=c.version.version_id,
        portrait_id=c.portrait_id,
        generation_id=c.generation_id,
        source_note="supplied frame",
        retain_findings=True,
    )
    packet = result()
    provider = Mock(
        compare=AsyncMock(
            return_value=ComparisonOutput("synthetic-model", "fixture-v1", packet.findings)
        )
    )
    return InvestigationRuntime(similarity, provider), command


@pytest.mark.asyncio
async def test_history_retry_after_query_clear_and_changed_intent_conflict(
    session: AsyncSession, workspace: UUID
) -> None:
    active, command = await setup(session, workspace)
    actor = WorkflowActor(actor_ref="viewer", kind="human")
    packet = await generate(session, workspace, actor, command, active)
    await clear(session, workspace, actor, command.query_id, active.similarity)
    replay = await generate(session, workspace, actor, command, replace(active, provider=None))
    assert replay == packet
    with pytest.raises(ConflictError):
        await generate(
            session, workspace, actor, command.model_copy(update={"source_note": "changed"}), active
        )
    page = await read_history(
        session,
        workspace,
        actor,
        InvestigationHistory(version_id=command.version_id),
        replace(active, provider=None),
    )
    assert page.items == (packet,)
    async with session.begin():
        rows = list(await session.scalars(select(InvestigationRecord)))
        assert len(rows) == 1 and packet.source_note.encode() not in rows[0].ciphertext


@pytest.mark.asyncio
async def test_foreign_workspace_and_immutable_history(
    session: AsyncSession, workspace: UUID
) -> None:
    active, command = await setup(session, workspace)
    actor = WorkflowActor(actor_ref="viewer", kind="human")
    packet = await generate(session, workspace, actor, command, active)
    with pytest.raises(AccessDeniedError):
        await read_history(
            session, uuid4(), actor, InvestigationHistory(version_id=command.version_id), active
        )
    with pytest.raises(DBAPIError):
        async with session.begin():
            await session.execute(
                update(InvestigationRecord)
                .where(InvestigationRecord.id == packet.id)
                .values(ordinal=999)
            )


@pytest.mark.asyncio
async def test_saved_review_request_exact_version_replay_and_immutable_receipt(
    session: AsyncSession, workspace: UUID
) -> None:
    active, command = await setup(session, workspace)
    actor = WorkflowActor(actor_ref="viewer", kind="human")
    packet = await generate(session, workspace, actor, command, active)
    intent = InvestigationReviewCommand(
        request_id=uuid4(), version_id=packet.version_id, investigation_id=packet.id
    )
    receipt = await request_review(session, workspace, actor, intent)
    assert await request_review(session, workspace, actor, intent) == receipt
    assert receipt.state == "requested" and receipt.requester_ref == actor.actor_ref
    async with session.begin():
        event = await session.scalar(select(Event).where(Event.resource_id == str(receipt.id)))
        assert event is not None and event.resource_type == "persona_investigation_review"
        assert event.actor_id == actor.actor_ref and event.source == "server"
        assert event.metadata_ == {"operation": "investigation_review_requested"}
    with pytest.raises(ConflictError):
        await request_review(
            session, workspace, actor, intent.model_copy(update={"investigation_id": uuid4()})
        )
    with pytest.raises(AccessDeniedError):
        await request_review(
            session,
            workspace,
            actor,
            intent.model_copy(update={"request_id": uuid4(), "investigation_id": uuid4()}),
        )
    page = await request_history(
        session, workspace, actor, InvestigationHistory(version_id=packet.version_id)
    )
    assert page.items == (receipt,)
    with pytest.raises(DBAPIError):
        async with session.begin():
            await session.execute(
                update(InvestigationReviewRequest)
                .where(InvestigationReviewRequest.id == receipt.id)
                .values(ordinal=999)
            )
