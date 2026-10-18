"""Authorized immutable projections for passports; no ciphertext or review comments."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import AssetSnapshot
from accord.personas.campaign_models import CampaignDecision, CampaignOffer, PersonaAsset
from accord.personas.campaign_repository import offer_row
from accord.personas.models import Persona, Version
from accord.personas.passport_contracts import AssetPage
from accord.personas.repository import AccessDeniedError
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import authorize_actor, locked_version


async def campaign_access(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    campaign: UUID,
) -> tuple[CampaignOffer, Version, Persona]:
    await authorize_actor(session, workspace, actor, None)
    offer = await offer_row(session, workspace, campaign)
    if actor.actor_ref not in {offer.owner_ref, offer.recipient_ref}:
        raise AccessDeniedError("passport access denied")
    version, persona = await locked_version(session, workspace, offer.version_id)
    return offer, version, persona


def observation(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, campaign: UUID, version: UUID
) -> None:
    session.add(
        decision_event(
            workspace_id=workspace,
            actor_ref=actor.actor_ref,
            request_id=uuid4(),
            record_id=campaign,
            version_id=version,
            event_id=uuid4().hex,
            recorded_at=datetime.now(UTC),
            action="persona.workflow_observed",
        )
    )


async def accepted_binding(
    session: AsyncSession,
    workspace: UUID,
    campaign: UUID,
    acceptance: UUID,
    issued: datetime,
) -> bool:
    return (
        await session.scalar(
            select(CampaignDecision.id).where(
                CampaignDecision.workspace_id == workspace,
                CampaignDecision.campaign_id == campaign,
                CampaignDecision.id == acceptance,
                CampaignDecision.decision == "accepted",
                CampaignDecision.recorded_at <= issued,
            )
        )
        is not None
    )


async def assets(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    version_id: UUID,
) -> AssetPage:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, "creator")
        _, persona = await locked_version(session, workspace, version_id)
        if persona.owner_ref != actor.actor_ref:
            raise AccessDeniedError("asset catalogue requires persona owner")
        rows = tuple(
            await session.scalars(
                select(PersonaAsset)
                .where(
                    PersonaAsset.workspace_id == workspace,
                    PersonaAsset.version_id == version_id,
                )
                .order_by(PersonaAsset.id)
                .limit(21)
            )
        )
        if len(rows) > 20:
            raise RuntimeError("asset catalogue exceeds the supported bound")
        result = AssetPage(
            workspace_id=workspace,
            version_id=version_id,
            assets=tuple(AssetSnapshot(id=r.id, digest=r.digest, label=r.label) for r in rows),
        )
        observation(session, workspace, actor, version_id, version_id)
        await authorize_actor(session, workspace, actor, "creator")
    return result
