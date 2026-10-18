"""Server time, not caller payloads, gates acceptance and current eligibility."""

from datetime import UTC, datetime, tzinfo
from typing import Self
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import campaign_decisions, campaign_status
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_status import inspect_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.repository import ConflictError
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.workflow_fixtures import human


async def test_expiry_withdraws_use_and_refuses_new_acceptance(
    session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    intent = offer_intent(version.version_id, review.id, ids)
    offer = await offer_campaign(session, workspace, human("creator-a"), intent)
    pending = await offer_campaign(
        session,
        workspace,
        human("creator-a"),
        offer_intent(version.version_id, review.id, ids, scope=intent.scope),
    )
    choice = decision_intent(offer.id)
    accepted = await decide_campaign(session, workspace, human("reviewer-b"), choice)

    class ExpiredClock(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            return cls.fromtimestamp(offer.scope.ends_at.timestamp(), tz or UTC)

    monkeypatch.setattr(campaign_status, "datetime", ExpiredClock)
    monkeypatch.setattr(campaign_decisions, "datetime", ExpiredClock)
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert status.blocking_reasons == ("expired",) and not status.eligible_for_use
    with pytest.raises(ConflictError, match="expired"):
        await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(pending.id))
    assert await decide_campaign(session, workspace, human("reviewer-b"), choice) == accepted
    assert await offer_campaign(session, workspace, human("creator-a"), intent) == offer
