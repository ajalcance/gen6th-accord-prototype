"""Creator-authorized campaign offers bound to exact reviewed versions."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignReceipt, OfferCampaignCommand
from accord.personas.campaign_models import CampaignAsset, CampaignOffer
from accord.personas.campaign_repository import campaign_receipt, scoped_assets
from accord.personas.lifecycle_policy import lifecycle_blocks
from accord.personas.production_evidence import require_supporting_evidence
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import (
    authorize_actor,
    has_role,
    latest_review,
    locked_version,
    require_current,
)


async def _replay_offer(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, command: OfferCampaignCommand
) -> CampaignOffer | None:
    rows = await session.scalars(
        select(CampaignOffer).where(
            CampaignOffer.workspace_id == workspace_id,
            CampaignOffer.owner_ref == actor_ref,
            CampaignOffer.request_id == command.request_id,
        )
    )
    row = rows.one_or_none()
    if row is not None and row.fingerprint != fingerprint(command):
        raise ConflictError("campaign request ID already used for different content")
    return row


async def _validate_offer(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, command: OfferCampaignCommand
) -> None:
    review = await latest_review(session, workspace_id, command.version_id)
    if review is None or review.id != command.review_id or review.decision != "approved":
        raise ConflictError("campaign requires the current approved review")
    if not await has_role(session, workspace_id, review.reviewer_ref, "reviewer"):
        raise AccessDeniedError("reviewer permission no longer available")
    if command.scope.recipient_ref == actor_ref or not await has_role(
        session, workspace_id, command.scope.recipient_ref, "reviewer"
    ):
        raise AccessDeniedError("campaign requires an independent permitted recipient")
    if command.scope.ends_at <= datetime.now(UTC):
        raise ConflictError("campaign scope has expired")
    await scoped_assets(session, workspace_id, command.version_id, command.scope.asset_ids)
    await require_supporting_evidence(
        session, workspace_id, command.version_id, actor_ref, command.scope.production
    )


async def _append_offer(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, command: OfferCampaignCommand
) -> CampaignOffer:
    values = command.scope.model_dump(exclude={"asset_ids", "production"})
    row = CampaignOffer(
        id=uuid4(),
        workspace_id=workspace_id,
        version_id=command.version_id,
        review_id=command.review_id,
        owner_ref=actor_ref,
        request_id=command.request_id,
        fingerprint=fingerprint(command),
        recorded_at=datetime.now(UTC),
        event_id=uuid4().hex,
        production=(
            command.scope.production.model_dump(mode="json") if command.scope.production else None
        ),
        **values,
    )
    session.add(
        decision_event(
            workspace_id=workspace_id,
            actor_ref=actor_ref,
            request_id=command.request_id,
            record_id=row.id,
            version_id=row.version_id,
            event_id=row.event_id,
            recorded_at=row.recorded_at,
            action="persona.campaign_offered",
        )
    )
    session.add(row)
    await session.flush()
    session.add_all(
        [
            CampaignAsset(
                workspace_id=workspace_id,
                campaign_id=row.id,
                version_id=row.version_id,
                asset_id=asset_id,
            )
            for asset_id in command.scope.asset_ids
        ]
    )
    await session.flush()
    return row


async def offer_campaign(
    session: AsyncSession, workspace_id: UUID, actor: WorkflowActor, command: OfferCampaignCommand
) -> CampaignReceipt:
    """Commit creator permission, exact asset bindings and server event together."""
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, "creator")
        version, persona = await locked_version(session, workspace_id, command.version_id)
        if persona.owner_ref != actor.actor_ref:
            raise AccessDeniedError("campaign requires persona owner permission")
        row = await _replay_offer(session, workspace_id, actor.actor_ref, command)
        if row is None:
            require_current(version, persona)
            if await lifecycle_blocks(
                session,
                workspace_id,
                persona.id,
                version.id,
                command.scope.production,
                command.scope.starts_at,
                command.scope.ends_at,
            ):
                raise ConflictError(
                    "production requires current operator, rights and content assessments"
                )
            await _validate_offer(session, workspace_id, actor.actor_ref, command)
            row = await _append_offer(session, workspace_id, actor.actor_ref, command)
        result = await campaign_receipt(session, row)
        await authorize_actor(session, workspace_id, actor, "creator")
    return result
