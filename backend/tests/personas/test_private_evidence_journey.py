"""Internal PostgreSQL workflow, explicitly not an authenticated browser/API journey."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_models import PersonaAsset
from accord.personas.campaign_status import inspect_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.evidence_service import enqueue, inspect_evidence
from accord.personas.repository import AccessDeniedError
from accord.personas.reviews import record_review
from personas.campaign_fixtures import decision_intent, offer_intent
from personas.private_evidence_fixtures import (
    EphemeralTestWrapper,
    FixtureContentInspector,
    chunks,
    intent,
)
from personas.workflow_fixtures import draft_for_review, human, review_intent


async def seed_asset(session: AsyncSession, workspace: UUID, version_id: UUID) -> UUID:
    asset_id = uuid4()
    session.add(
        PersonaAsset(
            id=asset_id,
            workspace_id=workspace,
            version_id=version_id,
            digest="a" * 64,
            label="Separate fictional campaign illustration",
        )
    )
    await session.commit()
    return asset_id


async def test_creation_private_evidence_review_and_fixture_campaign(
    session: AsyncSession, workspace: UUID
) -> None:
    version = await draft_for_review(session, workspace)
    owner, reviewer, recipient = human("creator-a"), human("reviewer-a"), human("reviewer-b")
    wrapper = EphemeralTestWrapper()
    evidence = await enqueue(
        session, workspace, owner, intent(version.version_id), chunks(), wrapper
    )
    inspected = await inspect_evidence(
        session, workspace, owner, evidence.id, wrapper, FixtureContentInspector()
    )
    assert inspected.state == "clean"
    review = await record_review(session, workspace, reviewer, review_intent(version.version_id))
    with pytest.raises(AccessDeniedError):
        await offer_campaign(
            session, workspace, owner, offer_intent(version.version_id, review.id, (evidence.id,))
        )
    asset_id = await seed_asset(session, workspace, version.version_id)
    offer = await offer_campaign(
        session, workspace, owner, offer_intent(version.version_id, review.id, (asset_id,))
    )
    assert not (await inspect_campaign(session, workspace, owner, offer.id)).eligible_for_use
    accepted = await decide_campaign(session, workspace, recipient, decision_intent(offer.id))
    assert (await inspect_campaign(session, workspace, recipient, offer.id)).eligible_for_use
    await decide_campaign(
        session,
        workspace,
        owner,
        decision_intent(
            offer.id,
            expected_previous_id=accepted.id,
            decision="revoked",
        ),
    )
    status = await inspect_campaign(session, workspace, owner, offer.id)
    assert not status.eligible_for_use and "revoked" in status.blocking_reasons
