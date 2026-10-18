"""Independent recipient decisions and creator revocation; append-only and atomic."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignDecisionCommand, CampaignDecisionReceipt
from accord.personas.campaign_models import CampaignDecision, CampaignOffer
from accord.personas.campaign_repository import (
    campaign_receipt,
    decision_receipt,
    latest_campaign_decision,
    offer_row,
)
from accord.personas.campaign_status import permission_blocks
from accord.personas.models import Persona, Version
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import authorize_actor, has_role, locked_version


async def _authorize_decision(
    session: AsyncSession, row: CampaignOffer, actor_ref: str, command: CampaignDecisionCommand
) -> None:
    owner_action = command.decision == "revoked"
    required_actor = row.owner_ref if owner_action else row.recipient_ref
    required_role = "creator" if owner_action else "reviewer"
    if actor_ref != required_actor or not await has_role(
        session, row.workspace_id, actor_ref, required_role
    ):
        raise AccessDeniedError("campaign decision permission denied")


async def _replay_decision(
    session: AsyncSession, workspace_id: UUID, actor_ref: str, command: CampaignDecisionCommand
) -> CampaignDecision | None:
    rows = await session.scalars(
        select(CampaignDecision).where(
            CampaignDecision.workspace_id == workspace_id,
            CampaignDecision.actor_ref == actor_ref,
            CampaignDecision.request_id == command.request_id,
        )
    )
    row = rows.one_or_none()
    if row is not None and row.fingerprint != fingerprint(command):
        raise ConflictError("campaign decision request ID already used for different content")
    return row


async def _validate_transition(
    session: AsyncSession,
    row: CampaignOffer,
    version: Version,
    persona: Persona,
    previous: CampaignDecision | None,
    command: CampaignDecisionCommand,
) -> None:
    if (previous.id if previous else None) != command.expected_previous_id:
        raise ConflictError("campaign decision changed")
    if previous is not None and previous.decision == "revoked":
        raise ConflictError("revoked campaigns require a new offer")
    if command.decision == "revoked":
        return
    if previous is not None and (
        previous.decision == "changes_requested" or command.decision == "accepted"
    ):
        raise ConflictError("campaign requires a new offer")
    if command.decision == "accepted":
        if await permission_blocks(session, row, version, persona):
            raise ConflictError("campaign permission is no longer current")
        if row.ends_at <= datetime.now(UTC):
            raise ConflictError("campaign scope has expired")
        await campaign_receipt(session, row)


async def _append_decision(
    session: AsyncSession,
    offer: CampaignOffer,
    actor_ref: str,
    command: CampaignDecisionCommand,
    previous: CampaignDecision | None,
) -> CampaignDecision:
    row = CampaignDecision(
        id=uuid4(),
        workspace_id=offer.workspace_id,
        campaign_id=offer.id,
        ordinal=previous.ordinal + 1 if previous else 1,
        actor_ref=actor_ref,
        request_id=command.request_id,
        fingerprint=fingerprint(command),
        decision=command.decision,
        statement=command.statement,
        recorded_at=datetime.now(UTC),
        event_id=uuid4().hex,
    )
    session.add(
        decision_event(
            workspace_id=offer.workspace_id,
            actor_ref=actor_ref,
            request_id=command.request_id,
            record_id=row.id,
            version_id=offer.version_id,
            event_id=row.event_id,
            recorded_at=row.recorded_at,
            action="persona.campaign_decided",
        )
    )
    session.add(row)
    await session.flush()
    return row


async def decide_campaign(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    command: CampaignDecisionCommand,
) -> CampaignDecisionReceipt:
    """Reauthorize retries; serialize every transition with persona edits/reviews."""
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, None)
        offer = await offer_row(session, workspace_id, command.campaign_id)
        await _authorize_decision(session, offer, actor.actor_ref, command)
        version, persona = await locked_version(session, workspace_id, offer.version_id)
        row = await _replay_decision(session, workspace_id, actor.actor_ref, command)
        if row is None:
            previous = await latest_campaign_decision(session, workspace_id, offer.id)
            await _validate_transition(session, offer, version, persona, previous, command)
            row = await _append_decision(session, offer, actor.actor_ref, command, previous)
        result = decision_receipt(row)
    return result
