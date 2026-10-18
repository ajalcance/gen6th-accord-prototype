"""Real database decision receipts, sealing, expiry and private inspection."""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.consumer import purge_expired
from accord.command.detection import evaluate_once
from accord.command.models import Event
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_evidence import inspect_workflow_evidence
from accord.personas.workflow_evidence_contracts import RecordKind
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.workflow_fixtures import human


async def test_each_decision_has_pending_then_audit_only_evidence(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    accepted = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(offer.id)
    )
    references: tuple[tuple[UUID, RecordKind], ...] = (
        (review.id, "review"),
        (offer.id, "campaign_offer"),
        (accepted.id, "campaign_decision"),
    )
    for record_id, kind in references:
        pending = await inspect_workflow_evidence(
            session, workspace, human("creator-a"), record_id, kind
        )
        assert pending.audit_state == "pending" and pending.cold_event_present
        assert (
            pending.anchor.record_id == record_id
            and pending.anchor.version_id == version.version_id
        )
    assert await seal_new(session) == 7
    async with session.begin():
        await session.execute(update(Event).values(ts=datetime.now(UTC) - timedelta(days=365)))
    assert await evaluate_once(session) == 7
    assert await purge_expired(session) == 7
    for record_id, kind in references:
        retained = await inspect_workflow_evidence(
            session, workspace, human("creator-a"), record_id, kind
        )
        assert retained.audit_state == "entry_present" and not retained.cold_event_present
        assert retained.audit_sequence is not None and retained.audit_entry_hash is not None
    assert await verify_chain(session) == (True, None, 7)


@pytest.mark.parametrize("kind", ["campaign_offer", "campaign_decision"])
async def test_campaign_evidence_is_private_to_parties(
    session: AsyncSession, workspace: UUID, kind: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    accepted = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(offer.id)
    )
    record_id = offer.id if kind == "campaign_offer" else accepted.id
    with pytest.raises(AccessDeniedError, match="evidence access"):
        await inspect_workflow_evidence(
            session, workspace, human("viewer"), record_id, cast(RecordKind, kind)
        )


async def test_cross_workspace_evidence_is_denied(session: AsyncSession, workspace: UUID) -> None:
    _version, review, _ids = await campaign_material(session, workspace)
    other = uuid4()
    session.add(WorkspaceMember(workspace_id=other, actor_ref="creator-a", role="creator"))
    await session.commit()
    with pytest.raises(AccessDeniedError):
        await inspect_workflow_evidence(session, other, human("creator-a"), review.id, "review")


async def test_missing_decision_evidence_fails_closed(
    session: AsyncSession, workspace: UUID
) -> None:
    _version, review, _ids = await campaign_material(session, workspace)
    async with session.begin():
        await session.execute(delete(Event).where(Event.event_id == review.event_id))
    with pytest.raises(RuntimeError, match="unavailable"):
        await inspect_workflow_evidence(session, workspace, human("creator-a"), review.id, "review")


async def test_nonserver_decision_evidence_fails_closed(
    session: AsyncSession, workspace: UUID
) -> None:
    _version, review, _ids = await campaign_material(session, workspace)
    async with session.begin():
        await session.execute(
            update(Event).where(Event.event_id == review.event_id).values(source="client")
        )
    with pytest.raises(RuntimeError, match="server observation"):
        await inspect_workflow_evidence(session, workspace, human("creator-a"), review.id, "review")
