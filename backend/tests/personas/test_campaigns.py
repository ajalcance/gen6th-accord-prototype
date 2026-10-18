"""Owner offers and independent campaign acceptance on actual PostgreSQL."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.audit import seal_new, verify_chain
from accord.command.models import Event
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_models import CampaignDecision, CampaignOffer
from accord.personas.campaign_status import inspect_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.reviews import record_review
from accord.personas.workflow_contracts import WorkflowActor
from personas.campaign_fixtures import (
    campaign_material,
    campaign_scope,
    decision_intent,
    offer_intent,
)
from personas.workflow_fixtures import human, review_intent


async def test_offer_accept_exact_retry_and_audit(session: AsyncSession, workspace: UUID) -> None:
    version, review, ids = await campaign_material(session, workspace)
    intent = offer_intent(version.version_id, review.id, ids)
    offer = await offer_campaign(session, workspace, human("creator-a"), intent)
    assert await offer_campaign(session, workspace, human("creator-a"), intent) == offer
    assert offer.scope == intent.scope and tuple(asset.id for asset in offer.assets) == ids
    pending = await inspect_campaign(session, workspace, human("reviewer-b"), offer.id)
    assert pending.blocking_reasons == ("awaiting_acceptance",)
    choice = decision_intent(offer.id)
    accepted = await decide_campaign(session, workspace, human("reviewer-b"), choice)
    assert await decide_campaign(session, workspace, human("reviewer-b"), choice) == accepted
    active = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert active.eligible_for_use and active.latest_decision == accepted
    assert await session.scalar(select(func.count()).select_from(CampaignOffer)) == 1
    assert await session.scalar(select(func.count()).select_from(CampaignDecision)) == 1
    events = list(await session.scalars(select(Event)))
    assert all(event.source == "server" for event in events)
    assert all(
        "conditions" not in event.metadata_ and "statement" not in event.metadata_
        for event in events
    )
    await session.rollback()
    assert await seal_new(session) == 6
    assert await verify_chain(session) == (True, None, 6)


@pytest.mark.parametrize("actor", ["creator-b", "reviewer-a", "reviewer-b", "viewer"])
async def test_only_owner_creator_can_offer(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    with pytest.raises(AccessDeniedError):
        await offer_campaign(
            session, workspace, human(actor), offer_intent(version.version_id, review.id, ids)
        )


@pytest.mark.parametrize("actor", ["creator-a", "creator-b", "reviewer-a", "viewer"])
async def test_only_named_recipient_can_accept(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    with pytest.raises(AccessDeniedError):
        await decide_campaign(session, workspace, human(actor), decision_intent(offer.id))


@pytest.mark.parametrize("kind", ["agent", "service"])
async def test_nonhuman_context_cannot_offer_or_accept(
    session: AsyncSession, workspace: UUID, kind: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    actor = WorkflowActor.model_validate({"actor_ref": "creator-a", "kind": kind})
    intent = offer_intent(version.version_id, review.id, ids)
    with pytest.raises(AccessDeniedError):
        await offer_campaign(session, workspace, actor, intent)
    offer = await offer_campaign(session, workspace, human("creator-a"), intent)
    actor = WorkflowActor.model_validate({"actor_ref": "reviewer-b", "kind": kind})
    with pytest.raises(AccessDeniedError):
        await decide_campaign(session, workspace, actor, decision_intent(offer.id))


async def test_changed_offer_and_decision_retry_conflict(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    intent = offer_intent(version.version_id, review.id, ids)
    offer = await offer_campaign(session, workspace, human("creator-a"), intent)
    changed = type(intent).model_validate(
        {**intent.model_dump(), "scope": campaign_scope(ids, purpose="Changed purpose")}
    )
    with pytest.raises(ConflictError, match="different content"):
        await offer_campaign(session, workspace, human("creator-a"), changed)
    choice = decision_intent(offer.id)
    await decide_campaign(session, workspace, human("reviewer-b"), choice)
    with pytest.raises(ConflictError, match="different content"):
        await decide_campaign(
            session,
            workspace,
            human("reviewer-b"),
            decision_intent(
                offer.id,
                request_id=choice.request_id,
                statement="Changed statement",
            ),
        )


async def test_scope_requires_current_approved_review_and_version_assets(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    with pytest.raises(ConflictError, match="approved review"):
        await offer_campaign(
            session, workspace, human("creator-a"), offer_intent(version.version_id, uuid4(), ids)
        )
    with pytest.raises(AccessDeniedError, match="assets"):
        await offer_campaign(
            session,
            workspace,
            human("creator-a"),
            offer_intent(version.version_id, review.id, (uuid4(),)),
        )
    with pytest.raises(AccessDeniedError, match="independent"):
        await offer_campaign(
            session,
            workspace,
            human("creator-a"),
            offer_intent(
                version.version_id,
                review.id,
                ids,
                scope=campaign_scope(ids, recipient_ref="creator-a"),
            ),
        )
    changed = await record_review(
        session,
        workspace,
        human("reviewer-a"),
        review_intent(
            version.version_id,
            expected_previous_id=review.id,
            decision="changes_requested",
        ),
    )
    with pytest.raises(ConflictError, match="approved review"):
        await offer_campaign(
            session,
            workspace,
            human("creator-a"),
            offer_intent(version.version_id, changed.id, ids),
        )


@pytest.mark.parametrize("actor", ["viewer", "reviewer-a", "creator-b"])
async def test_campaign_scope_is_private_to_parties(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    with pytest.raises(AccessDeniedError, match="campaign access"):
        await inspect_campaign(session, workspace, human(actor), offer.id)
