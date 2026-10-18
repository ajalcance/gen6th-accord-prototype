"""Withdrawal, expiry and stale permission must never resurrect fixture use."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_status import inspect_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.models import WorkspaceMember
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.reviews import record_review
from accord.personas.service import save
from personas.campaign_fixtures import (
    campaign_material,
    campaign_scope,
    decision_intent,
    offer_intent,
)
from personas.conftest import command
from personas.workflow_fixtures import human, review_intent


async def test_owner_revocation_is_final_and_historical_retry_is_not_permission(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    intent = offer_intent(version.version_id, review.id, ids)
    offer = await offer_campaign(session, workspace, human("creator-a"), intent)
    choice = decision_intent(offer.id)
    accepted = await decide_campaign(session, workspace, human("reviewer-b"), choice)
    with pytest.raises(AccessDeniedError):
        await decide_campaign(
            session,
            workspace,
            human("reviewer-b"),
            decision_intent(
                offer.id,
                decision="revoked",
                expected_previous_id=accepted.id,
            ),
        )
    revoke_intent = decision_intent(offer.id, decision="revoked", expected_previous_id=accepted.id)
    revoked = await decide_campaign(session, workspace, human("creator-a"), revoke_intent)
    assert revoked.ordinal == 2
    assert await decide_campaign(session, workspace, human("creator-a"), revoke_intent) == revoked
    assert await decide_campaign(session, workspace, human("reviewer-b"), choice) == accepted
    assert await offer_campaign(session, workspace, human("creator-a"), intent) == offer
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert status.blocking_reasons == ("revoked",) and not status.eligible_for_use
    with pytest.raises(ConflictError, match="new offer"):
        await decide_campaign(
            session,
            workspace,
            human("reviewer-b"),
            decision_intent(
                offer.id,
                expected_previous_id=revoked.id,
            ),
        )


async def test_recipient_change_request_withdraws_acceptance(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    first = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(offer.id)
    )
    with pytest.raises(ConflictError, match="decision changed"):
        await decide_campaign(
            session,
            workspace,
            human("reviewer-b"),
            decision_intent(offer.id, decision="changes_requested"),
        )
    changed = await decide_campaign(
        session,
        workspace,
        human("reviewer-b"),
        decision_intent(
            offer.id,
            decision="changes_requested",
            expected_previous_id=first.id,
        ),
    )
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert status.latest_decision == changed and status.blocking_reasons == ("changes_requested",)
    with pytest.raises(ConflictError, match="new offer"):
        await decide_campaign(
            session,
            workspace,
            human("reviewer-b"),
            decision_intent(
                offer.id,
                expected_previous_id=changed.id,
            ),
        )


async def test_version_edit_invalidates_active_and_pending_campaigns(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    pending = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
    await save(
        session, workspace, "creator-a", command(persona_id=version.persona_id, expected_revision=1)
    )
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert "stale_version" in status.blocking_reasons and not status.eligible_for_use
    with pytest.raises(ConflictError, match="no longer current"):
        await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(pending.id))
    with pytest.raises(ConflictError, match="no longer current"):
        await offer_campaign(
            session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
        )


async def test_review_replacement_never_revives_old_campaign(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
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
    replacement = await record_review(
        session,
        workspace,
        human("reviewer-a"),
        review_intent(
            version.version_id,
            expected_previous_id=changed.id,
        ),
    )
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert status.blocking_reasons == ("review_changed",)
    with pytest.raises(ConflictError, match="approved review"):
        await offer_campaign(
            session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
        )
    renewed = await offer_campaign(
        session,
        workspace,
        human("creator-a"),
        offer_intent(version.version_id, replacement.id, ids),
    )
    assert renewed.review_id == replacement.id and renewed.id != offer.id


@pytest.mark.parametrize(
    "actor,reason",
    [
        ("creator-a", "owner_permission_removed"),
        ("reviewer-a", "reviewer_permission_removed"),
        ("reviewer-b", "recipient_permission_removed"),
    ],
)
async def test_removed_membership_role_withdraws_current_eligibility(
    session: AsyncSession, workspace: UUID, actor: str, reason: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    choice = decision_intent(offer.id)
    await decide_campaign(session, workspace, human("reviewer-b"), choice)
    await session.execute(
        update(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == workspace,
            WorkspaceMember.actor_ref == actor,
        )
        .values(role="viewer")
    )
    await session.commit()
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert reason in status.blocking_reasons and not status.eligible_for_use
    if actor == "reviewer-b":
        with pytest.raises(AccessDeniedError):
            await decide_campaign(session, workspace, human("reviewer-b"), choice)


async def test_future_window_can_be_accepted_but_is_not_yet_eligible(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    now = datetime.now(UTC)
    scope = campaign_scope(ids, starts_at=now + timedelta(days=1), ends_at=now + timedelta(days=2))
    offer = await offer_campaign(
        session,
        workspace,
        human("creator-a"),
        offer_intent(version.version_id, review.id, ids, scope=scope),
    )
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
    status = await inspect_campaign(session, workspace, human("creator-a"), offer.id)
    assert status.blocking_reasons == ("not_started",)


async def test_expired_scope_is_never_offered(session: AsyncSession, workspace: UUID) -> None:
    version, review, ids = await campaign_material(session, workspace)
    now = datetime.now(UTC)
    scope = campaign_scope(ids, starts_at=now - timedelta(days=2), ends_at=now - timedelta(days=1))
    with pytest.raises(ConflictError, match="expired"):
        await offer_campaign(
            session,
            workspace,
            human("creator-a"),
            offer_intent(version.version_id, review.id, ids, scope=scope),
        )
