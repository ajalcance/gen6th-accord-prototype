"""Resolve an immutable decision reference only within its authorized workspace."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_models import CampaignDecision, CampaignOffer
from accord.personas.campaign_repository import offer_row
from accord.personas.repository import AccessDeniedError
from accord.personas.review_models import ReviewRecord
from accord.personas.workflow_evidence_contracts import DecisionAction, DecisionAnchor, RecordKind


def _anchor(
    row: ReviewRecord | CampaignOffer | CampaignDecision,
    version_id: UUID,
    actor_ref: str,
    action: DecisionAction,
) -> DecisionAnchor:
    return DecisionAnchor(
        record_id=row.id,
        workspace_id=row.workspace_id,
        version_id=version_id,
        actor_ref=actor_ref,
        action=action,
        recorded_at=row.recorded_at,
        write_request_id=row.request_id,
        event_id=row.event_id,
    )


def _require_party(offer: CampaignOffer, actor_ref: str) -> None:
    if actor_ref not in {offer.owner_ref, offer.recipient_ref}:
        raise AccessDeniedError("campaign evidence access denied")


async def decision_anchor(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, record_id: UUID, kind: RecordKind
) -> DecisionAnchor:
    if kind == "review":
        review = await session.scalar(
            select(ReviewRecord).where(
                ReviewRecord.workspace_id == workspace_id,
                ReviewRecord.id == record_id,
            )
        )
        if review is None:
            raise AccessDeniedError("review evidence access denied")
        return _anchor(review, review.version_id, review.reviewer_ref, "persona.review_recorded")
    if kind == "campaign_offer":
        offer = await offer_row(session, workspace_id, record_id)
        _require_party(offer, actor_ref)
        return _anchor(offer, offer.version_id, offer.owner_ref, "persona.campaign_offered")
    if kind != "campaign_decision":
        raise AccessDeniedError("unknown decision evidence kind")
    decision = await session.scalar(
        select(CampaignDecision).where(
            CampaignDecision.workspace_id == workspace_id,
            CampaignDecision.id == record_id,
        )
    )
    if decision is None:
        raise AccessDeniedError("campaign evidence access denied")
    offer = await offer_row(session, workspace_id, decision.campaign_id)
    _require_party(offer, actor_ref)
    return _anchor(decision, offer.version_id, decision.actor_ref, "persona.campaign_decided")
