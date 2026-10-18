"""Current campaign eligibility is recomputed; historical receipts never grant use."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import BlockingReason, CampaignStatus
from accord.personas.campaign_models import CampaignOffer
from accord.personas.campaign_repository import (
    campaign_receipt,
    decision_receipt,
    latest_campaign_decision,
    offer_row,
)
from accord.personas.lifecycle_policy import lifecycle_blocks
from accord.personas.models import Persona, Version
from accord.personas.production_contracts import ProductionUse
from accord.personas.production_evidence import supporting_evidence_available
from accord.personas.repository import AccessDeniedError
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import (
    authorize_actor,
    has_role,
    latest_review,
    locked_version,
)


async def permission_blocks(
    session: AsyncSession, row: CampaignOffer, version: Version, persona: Persona
) -> list[BlockingReason]:
    reasons: list[BlockingReason] = []
    if persona.head_revision != version.revision:
        reasons.append("stale_version")
    review = await latest_review(session, row.workspace_id, row.version_id)
    if review is None or review.id != row.review_id or review.decision != "approved":
        reasons.append("review_changed")
    if review is not None and not await has_role(
        session, row.workspace_id, review.reviewer_ref, "reviewer"
    ):
        reasons.append("reviewer_permission_removed")
    if persona.owner_ref != row.owner_ref or not await has_role(
        session, row.workspace_id, row.owner_ref, "creator"
    ):
        reasons.append("owner_permission_removed")
    if not await has_role(session, row.workspace_id, row.recipient_ref, "reviewer"):
        reasons.append("recipient_permission_removed")
    production = (
        ProductionUse.model_validate(row.production) if row.production is not None else None
    )
    if not await supporting_evidence_available(
        session, row.workspace_id, row.version_id, row.owner_ref, production
    ):
        reasons.append("supporting_evidence_unavailable")
    reasons.extend(
        cast(
            list[BlockingReason],
            await lifecycle_blocks(
                session,
                row.workspace_id,
                persona.id,
                version.id,
                production,
                row.starts_at,
                row.ends_at,
            ),
        )
    )
    return reasons


async def current_status(
    session: AsyncSession, row: CampaignOffer, version: Version, persona: Persona
) -> CampaignStatus:
    receipt = await campaign_receipt(session, row)
    previous = await latest_campaign_decision(session, row.workspace_id, row.id)
    reasons = await permission_blocks(session, row, version, persona)
    if previous is None:
        reasons.append("awaiting_acceptance")
    elif previous.decision in {"changes_requested", "revoked"}:
        reasons.append(
            "changes_requested" if previous.decision == "changes_requested" else "revoked"
        )
    now = datetime.now(UTC)
    if now < row.starts_at:
        reasons.append("not_started")
    if now >= row.ends_at:
        reasons.append("expired")
    return CampaignStatus(
        receipt=receipt,
        latest_decision=decision_receipt(previous) if previous else None,
        evaluated_at=now,
        blocking_reasons=tuple(reasons),
        eligible_for_use=not reasons,
    )


async def inspect_campaign(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, campaign_id: UUID
) -> CampaignStatus:
    """Owner/recipient-only status read with an independently recorded observation."""
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, None)
        row = await offer_row(session, workspace_id, campaign_id)
        if actor.actor_ref not in {row.owner_ref, row.recipient_ref}:
            raise AccessDeniedError("campaign access denied")
        version, persona = await locked_version(session, workspace_id, row.version_id)
        result = await current_status(session, row, version, persona)
        session.add(
            decision_event(
                workspace_id=workspace_id,
                actor_ref=actor.actor_ref,
                request_id=request_id,
                record_id=row.id,
                version_id=row.version_id,
                event_id=uuid4().hex,
                recorded_at=datetime.now(UTC),
                action="persona.workflow_observed",
            )
        )
        await authorize_actor(session, workspace_id, actor, None)
    return result
