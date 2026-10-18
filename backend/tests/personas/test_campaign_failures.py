"""Atomic campaign rollback and tenant/version binding failures."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from accord.command.models import Event
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_models import (
    CampaignAsset,
    CampaignDecision,
    CampaignOffer,
    PersonaAsset,
)
from accord.personas.campaign_status import inspect_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError
from accord.personas.service import save
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.conftest import command
from personas.workflow_fixtures import human


def fail_binding(session: Session, _context: object, _instances: object) -> None:
    if any(isinstance(row, CampaignAsset) for row in session.new):
        raise RuntimeError("injected fixture binding failure")


def fail_decision(session: Session, _context: object, _instances: object) -> None:
    if any(isinstance(row, CampaignDecision) for row in session.new):
        raise RuntimeError("injected campaign decision failure")


async def test_late_asset_failure_rolls_back_offer_and_event(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    event.listen(session.sync_session, "before_flush", fail_binding)
    try:
        with pytest.raises(RuntimeError, match="binding failure"):
            await offer_campaign(
                session,
                workspace,
                human("creator-a"),
                offer_intent(version.version_id, review.id, ids),
            )
    finally:
        event.remove(session.sync_session, "before_flush", fail_binding)
    assert await session.scalar(select(func.count()).select_from(CampaignOffer)) == 0
    assert await session.scalar(select(func.count()).select_from(CampaignAsset)) == 0
    assert await session.scalar(select(func.count()).select_from(Event)) == 2


async def test_failed_acceptance_leaves_offer_pending(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    event.listen(session.sync_session, "before_flush", fail_decision)
    try:
        with pytest.raises(RuntimeError, match="decision failure"):
            await decide_campaign(
                session, workspace, human("reviewer-b"), decision_intent(offer.id)
            )
    finally:
        event.remove(session.sync_session, "before_flush", fail_decision)
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert status.blocking_reasons == ("awaiting_acceptance",)
    assert await session.scalar(select(func.count()).select_from(CampaignDecision)) == 0


async def test_assets_from_other_version_are_denied(session: AsyncSession, workspace: UUID) -> None:
    version, review, _ids = await campaign_material(session, workspace)
    other = await save(session, workspace, "creator-b", command())
    alien = uuid4()
    session.add(
        PersonaAsset(
            id=alien,
            workspace_id=workspace,
            version_id=other.version_id,
            digest="a" * 64,
            label="Different fictional version",
        )
    )
    await session.commit()
    with pytest.raises(AccessDeniedError, match="assets"):
        await offer_campaign(
            session,
            workspace,
            human("creator-a"),
            offer_intent(version.version_id, review.id, (alien,)),
        )


async def test_campaign_id_from_other_workspace_is_not_disclosed(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    other = uuid4()
    session.add(WorkspaceMember(workspace_id=other, actor_ref="creator-a", role="creator"))
    await session.commit()
    with pytest.raises(AccessDeniedError, match="campaign access"):
        await inspect_campaign(session, other, human("creator-a"), offer.id)
