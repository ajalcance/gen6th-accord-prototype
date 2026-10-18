"""Owner-approved allowlist, bounded signing, immutable replay and explicit unpublication."""

import asyncio
import base64
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignStatus
from accord.personas.campaign_models import CampaignOffer
from accord.personas.campaign_status import current_status
from accord.personas.issuance_models import (
    PassportIssuance,
    PassportPublication,
    PassportUnpublication,
)
from accord.personas.models import Persona, Version
from accord.personas.passport_contracts import PassportPayload, SignedPassport
from accord.personas.passport_repository import campaign_access, observation
from accord.personas.passport_service import export
from accord.personas.passport_signing import PassportRuntime, canonical
from accord.personas.photo_models import Portrait, VersionPortrait
from accord.personas.publication_contracts import (
    ApprovePublication,
    PublicationReceipt,
    PublicField,
    PublicProjection,
)
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import authorize_actor


def receipt(row: PassportPublication) -> PublicationReceipt:
    return PublicationReceipt(
        workspace_id=row.workspace_id,
        publication_id=row.id,
        path=f"/p/{row.workspace_id}/{row.id}",
        package=SignedPassport.model_validate(row.package),
    )


def mutation_event(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    publication: UUID,
    version: UUID,
    action: str,
) -> None:
    session.add(
        decision_event(
            workspace_id=workspace,
            actor_ref=actor.actor_ref,
            request_id=uuid4(),
            record_id=publication,
            version_id=version,
            event_id=uuid4().hex,
            recorded_at=datetime.now(UTC),
            action=action,
        )
    )


async def primary_portrait(
    session: AsyncSession, workspace: UUID, version: UUID
) -> Portrait | None:
    result = await session.scalar(
        select(Portrait)
        .join(
            VersionPortrait,
            (VersionPortrait.portrait_id == Portrait.id)
            & (VersionPortrait.workspace_id == Portrait.workspace_id),
        )
        .where(VersionPortrait.workspace_id == workspace, VersionPortrait.version_id == version)
    )
    return result


async def projection(
    session: AsyncSession,
    workspace: UUID,
    command: ApprovePublication,
    payload: PassportPayload,
    publication_id: UUID,
) -> PublicProjection:
    content = payload.version.content
    production = payload.campaign.scope.production
    if production is None:
        raise ConflictError("public passport requires production scope")
    values: dict[PublicField, str] = {
        "name": content.name,
        "biography": content.biography,
        "human_contribution": content.human_contribution,
        "ai_disclosure": content.ai_disclosure,
        "production_name": production.title,
        "purpose": payload.campaign.scope.purpose,
        "conditions": payload.campaign.scope.conditions,
    }
    if "portrait_sha256" in command.fields:
        photo = await primary_portrait(session, workspace, payload.version.version_id)
        if photo is None:
            raise ConflictError("public portrait requires a saved inspected portrait")
        values["portrait_sha256"] = photo.thumbnail_sha256
    return PublicProjection(
        publication_id=publication_id,
        approved_at=datetime.now(UTC),
        valid_from=payload.campaign.scope.starts_at,
        valid_until=payload.campaign.scope.ends_at,
        version_revision=payload.version.revision,
        values={key: values[key] for key in command.fields},
    )


async def owner_campaign(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, campaign: UUID
) -> tuple[CampaignOffer, Version, Persona]:
    await authorize_actor(session, workspace, actor, "creator")
    offer, version, persona = await campaign_access(session, workspace, actor, campaign)
    if offer.owner_ref != actor.actor_ref:
        raise AccessDeniedError("public approval requires the owner")
    return offer, version, persona


async def approve(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: ApprovePublication,
    runtime: PassportRuntime | None,
) -> PublicationReceipt:
    async with tracked_transaction(session, workspace, actor.actor_ref, command.request_id):
        await owner_campaign(session, workspace, actor, command.campaign_id)
    package = await export(session, workspace, actor, command.campaign_id, runtime)
    payload = PassportPayload.model_validate(package.payload)
    async with tracked_transaction(session, workspace, actor.actor_ref, command.request_id):
        context = await owner_campaign(session, workspace, actor, command.campaign_id)
        status = await current_status(session, *context)
        if (
            not status.eligible_for_use
            or status.latest_decision is None
            or status.latest_decision.id != payload.acceptance_id
        ):
            raise ConflictError("publication requires current accepted permission")
        existing = await session.scalar(
            select(PassportPublication).where(
                PassportPublication.workspace_id == workspace,
                PassportPublication.owner_ref == actor.actor_ref,
                PassportPublication.request_id == command.request_id,
            )
        )
        if existing is not None:
            await validate_approval_replay(session, existing, command)
            return receipt(existing)
        row = await new_approval(
            session, workspace, actor, command, payload, runtime, context, status
        )
        result = receipt(row)
    return result


async def sign_projection(public: PublicProjection, runtime: PassportRuntime) -> SignedPassport:
    if runtime.signer is None or not runtime.trust.contains(runtime.signer.key_id):
        raise RuntimeError("public signing unavailable")
    async with asyncio.timeout(25):
        signed = SignedPassport(
            key_id=runtime.signer.key_id,
            payload=public.model_dump(mode="json"),
            signature=base64.b64encode(
                await runtime.signer.sign(canonical(public.model_dump(mode="json")))
            ).decode(),
        )
    if runtime.trust.verify(signed) != "valid":
        raise RuntimeError("public signer not trusted")
    return signed


async def new_approval(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: ApprovePublication,
    payload: PassportPayload,
    runtime: PassportRuntime | None,
    context: tuple[CampaignOffer, Version, Persona],
    status: CampaignStatus,
) -> PassportPublication:
    if (
        runtime is None
        or runtime.signer is None
        or not runtime.trust.contains(runtime.signer.key_id)
    ):
        raise RuntimeError("public signing unavailable")
    issuance = await session.scalar(
        select(PassportIssuance).where(
            PassportIssuance.workspace_id == workspace,
            PassportIssuance.campaign_id == command.campaign_id,
            PassportIssuance.acceptance_id == payload.acceptance_id,
        )
    )
    if issuance is None:
        raise RuntimeError("persisted issuance required")
    public = await projection(session, workspace, command, payload, uuid4())
    signed = await sign_projection(public, runtime)
    await authorize_actor(session, workspace, actor, "creator")
    fresh = await current_status(session, *context)
    if not fresh.eligible_for_use or fresh.latest_decision != status.latest_decision:
        raise ConflictError("permission changed during public signing")
    row = PassportPublication(
        id=public.publication_id,
        workspace_id=workspace,
        issuance_id=issuance.id,
        owner_ref=actor.actor_ref,
        request_id=command.request_id,
        fingerprint=fingerprint(command),
        fields=list(command.fields),
        package=signed.model_dump(mode="json"),
        recorded_at=public.approved_at,
    )
    session.add(row)
    version_id = payload.version.version_id
    mutation_event(session, workspace, actor, row.id, version_id, "persona.publication_approved")
    return row


async def validate_approval_replay(
    session: AsyncSession, row: PassportPublication, command: ApprovePublication
) -> None:
    if row.fingerprint != fingerprint(command):
        raise ConflictError("publication approval intent changed")
    if await session.get(PassportUnpublication, row.id) is not None:
        raise ConflictError("withdrawn approval requires a new explicit intent")


async def unpublish(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, publication: UUID
) -> PublicationReceipt:
    async with tracked_transaction(session, workspace, actor.actor_ref, uuid4()):
        await authorize_actor(session, workspace, actor, "creator")
        row = await session.scalar(
            select(PassportPublication)
            .where(
                PassportPublication.workspace_id == workspace,
                PassportPublication.id == publication,
                PassportPublication.owner_ref == actor.actor_ref,
            )
            .with_for_update()
        )
        if row is None:
            raise AccessDeniedError("public approval access denied")
        issuance = await session.get(PassportIssuance, row.issuance_id)
        if issuance is None:
            raise RuntimeError("issuance missing")
        payload = PassportPayload.model_validate(
            SignedPassport.model_validate(issuance.package).payload
        )
        if await session.get(PassportUnpublication, publication) is None:
            session.add(
                PassportUnpublication(
                    publication_id=publication,
                    workspace_id=workspace,
                    owner_ref=actor.actor_ref,
                    recorded_at=datetime.now(UTC),
                )
            )
            mutation_event(
                session,
                workspace,
                actor,
                publication,
                payload.version.version_id,
                "persona.publication_revoked",
            )
        observation(session, workspace, actor, publication, payload.version.version_id)
        result = receipt(row)
    return result
