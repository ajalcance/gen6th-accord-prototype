"""Party privacy and stable campaign decision cursors."""

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignHistoryQuery
from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_history import campaign_history
from accord.personas.campaigns import offer_campaign
from accord.personas.repository import AccessDeniedError
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.workflow_fixtures import human


@pytest.mark.parametrize(
    "field,value",
    [
        ("limit", 0),
        ("limit", 101),
        ("limit", True),
        ("before_ordinal", 0),
        ("before_ordinal", True),
    ],
)
def test_campaign_history_bounds_are_strict(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        CampaignHistoryQuery.model_validate({"campaign_id": uuid4(), field: value})


async def test_campaign_history_retains_withdrawn_acceptance(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    query = CampaignHistoryQuery(campaign_id=offer.id, limit=1)
    empty = await campaign_history(session, workspace, human("creator-a"), query)
    assert empty.items == () and empty.next_before_ordinal is None
    accepted = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(offer.id)
    )
    revoked = await decide_campaign(
        session,
        workspace,
        human("creator-a"),
        decision_intent(
            offer.id,
            decision="revoked",
            expected_previous_id=accepted.id,
        ),
    )
    newest = await campaign_history(session, workspace, human("creator-a"), query)
    assert newest.items == (revoked,) and newest.next_before_ordinal == 2
    last = await campaign_history(
        session,
        workspace,
        human("reviewer-b"),
        CampaignHistoryQuery(
            campaign_id=offer.id,
            limit=1,
            before_ordinal=newest.next_before_ordinal,
        ),
    )
    assert last.items == (accepted,) and last.next_before_ordinal is None
    with pytest.raises(AccessDeniedError):
        await campaign_history(session, workspace, human("viewer"), query)
