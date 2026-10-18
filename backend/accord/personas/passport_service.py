"""Fresh permission at export and verification; historical signatures never grant current use."""

import asyncio
import base64
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_status import current_status
from accord.personas.capture_reads import reference_captures
from accord.personas.issuance_repository import remember_issuance, stored_issuance, validate_replay
from accord.personas.passport_contracts import (
    PassportPayload,
    PassportReadiness,
    PassportVerification,
    SignedPassport,
    VerifyPassport,
)
from accord.personas.passport_repository import accepted_binding, campaign_access, observation
from accord.personas.passport_signing import PassportRuntime, canonical
from accord.personas.repository import ConflictError, snapshot
from accord.personas.similarity_service import observation as workspace_observation
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor


async def readiness(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, runtime: PassportRuntime | None
) -> PassportReadiness:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, None)
        signer = runtime.signer if runtime else None
        result = PassportReadiness(
            workspace_id=workspace,
            export_available=bool(runtime and signer and runtime.trust.contains(signer.key_id)),
            verification_available=bool(runtime and runtime.trust.available()),
        )
        workspace_observation(session, workspace, actor, uuid4())
    return result


async def export(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    campaign: UUID,
    runtime: PassportRuntime | None,
) -> SignedPassport:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        offer, version, persona = await campaign_access(session, workspace, actor, campaign)
        status = await current_status(session, offer, version, persona)
        if not status.eligible_for_use or status.latest_decision is None:
            raise ConflictError("passport export requires current accepted permission")
        if runtime is None:
            raise RuntimeError("passport signing is unavailable")
        existing = await stored_issuance(session, workspace, campaign, status.latest_decision.id)
        if existing is not None:
            await validate_replay(session, workspace, version, status, existing, runtime)
            await authorize_actor(session, workspace, actor, None)
            fresh = await current_status(session, offer, version, persona)
            if not fresh.eligible_for_use or fresh.latest_decision != status.latest_decision:
                raise ConflictError("production permission changed during replay")
            observation(session, workspace, actor, campaign, version.id)
            return existing
        if runtime.signer is None or not runtime.trust.contains(runtime.signer.key_id):
            raise RuntimeError("passport signing is unavailable")
        references = await reference_captures(session, workspace, version.id)
        if status.receipt.scope.production is None or not references:
            raise ConflictError("passport export requires production scope and approved references")
        payload = PassportPayload(
            issued_at=datetime.now(UTC),
            version=snapshot(version),
            campaign=status.receipt,
            acceptance_id=status.latest_decision.id,
            references=references,
        )
        package = await sign_issuance(runtime, payload)
        await authorize_actor(session, workspace, actor, None)
        fresh = await current_status(session, offer, version, persona)
        if not fresh.eligible_for_use or fresh.latest_decision != status.latest_decision:
            raise ConflictError("production permission changed during signing")
        remember_issuance(session, workspace, actor, payload, package)
        observation(session, workspace, actor, campaign, version.id)
    return package


async def sign_issuance(runtime: PassportRuntime, payload: PassportPayload) -> SignedPassport:
    if runtime.signer is None:
        raise RuntimeError("passport signing is unavailable")
    try:
        async with asyncio.timeout(25):
            signature = await runtime.signer.sign(canonical(payload.model_dump(mode="json")))
        package = SignedPassport(
            key_id=runtime.signer.key_id,
            payload=payload.model_dump(mode="json"),
            signature=base64.b64encode(signature).decode(),
        )
    except Exception as exc:
        raise RuntimeError("passport signing is unavailable") from exc
    if runtime.trust.verify(package) != "valid":
        raise RuntimeError("passport signer is not trusted")
    return package


async def verify(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    command: VerifyPassport,
    runtime: PassportRuntime | None,
) -> PassportVerification:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, uuid4(), actor_type=actor.audit_type
    ):
        offer, version, persona = await campaign_access(
            session, workspace, actor, command.campaign_id
        )
        if runtime is None or not runtime.trust.available():
            raise RuntimeError("passport verification is unavailable")
        integrity = runtime.trust.verify(command.package)
        status = None
        if integrity == "valid":
            try:
                payload = PassportPayload.model_validate(command.package.payload)
                if canonical(payload.model_dump(mode="json")) != canonical(
                    dict(command.package.payload)
                ):
                    raise ValueError("noncanonical semantic fields")
            except (ValidationError, ValueError):
                integrity = "invalid_package"
            else:
                status = await current_status(session, offer, version, persona)
                references = await reference_captures(session, workspace, version.id)
                if (
                    payload.campaign != status.receipt
                    or payload.version != snapshot(version)
                    or payload.references != references
                    or payload.issued_at > datetime.now(UTC)
                    or payload.issued_at < offer.recorded_at
                    or not await accepted_binding(
                        session, workspace, offer.id, payload.acceptance_id, payload.issued_at
                    )
                ):
                    integrity, status = "binding_mismatch", None
        await authorize_actor(session, workspace, actor, None)
        observation(session, workspace, actor, command.campaign_id, version.id)
        result = PassportVerification(
            workspace_id=workspace,
            campaign_id=command.campaign_id,
            integrity=integrity,
            current_status=status,
        )
    return result
