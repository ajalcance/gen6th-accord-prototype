"""Independent decisions, concurrent revocation and retry serialization on PostgreSQL."""

import asyncio
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.personas.campaign_contracts import CampaignDecisionCommand, OfferCampaignCommand
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_models import CampaignDecision, CampaignOffer
from accord.personas.campaigns import offer_campaign
from accord.personas.repository import ConflictError
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.workflow_fixtures import human


async def offer(engine: AsyncEngine, workspace: UUID, intent: OfferCampaignCommand) -> object:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        return await offer_campaign(session, workspace, human("creator-a"), intent)


async def decide(
    engine: AsyncEngine, workspace: UUID, actor_ref: str, intent: CampaignDecisionCommand
) -> object:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        try:
            return await decide_campaign(session, workspace, human(actor_ref), intent)
        except ConflictError as exc:
            return exc


async def test_offer_exact_retry_commits_one_scope(
    db_engine: AsyncEngine, session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    intent = offer_intent(version.version_id, review.id, ids)
    results = await asyncio.wait_for(
        asyncio.gather(
            offer(db_engine, workspace, intent),
            offer(db_engine, workspace, intent),
        ),
        timeout=10,
    )
    assert results[0] == results[1]
    assert await session.scalar(select(func.count()).select_from(CampaignOffer)) == 1


async def test_acceptance_exact_retry_commits_one_decision(
    db_engine: AsyncEngine, session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    scope = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    intent = decision_intent(scope.id)
    results = await asyncio.wait_for(
        asyncio.gather(
            decide(db_engine, workspace, "reviewer-b", intent),
            decide(db_engine, workspace, "reviewer-b", intent),
        ),
        timeout=10,
    )
    assert results[0] == results[1]
    assert await session.scalar(select(func.count()).select_from(CampaignDecision)) == 1


async def test_acceptance_and_revocation_have_one_winner(
    db_engine: AsyncEngine, session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    scope = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    results = await asyncio.wait_for(
        asyncio.gather(
            decide(db_engine, workspace, "reviewer-b", decision_intent(scope.id)),
            decide(
                db_engine, workspace, "creator-a", decision_intent(scope.id, decision="revoked")
            ),
        ),
        timeout=10,
    )
    assert sum(isinstance(row, ConflictError) for row in results) == 1
    assert await session.scalar(select(func.count()).select_from(CampaignDecision)) == 1
