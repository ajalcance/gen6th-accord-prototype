"""Anonymous reads disclose only an explicitly approved projection, with fresh permission status."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.campaign_repository import offer_row
from accord.personas.campaign_status import current_status
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.issuance_models import (
    PassportIssuance,
    PassportPublication,
    PassportUnpublication,
)
from accord.personas.passport_contracts import PassportPayload, SignedPassport
from accord.personas.passport_signing import PassportRuntime, canonical
from accord.personas.photo_models import PortraitPayload
from accord.personas.photo_reads import decrypted_thumbnail
from accord.personas.publication_contracts import (
    PublicationPage,
    PublicProjection,
    PublicVerification,
)
from accord.personas.publication_service import primary_portrait
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_repository import locked_version


async def approved_row(
    session: AsyncSession, workspace: UUID, publication: UUID, runtime: PassportRuntime | None
) -> tuple[PassportPublication, PublicProjection, PassportPayload]:
    # A public identifier grants no workspace access. Every lookup is constrained by a stored grant.
    await session.execute(
        text("SELECT set_config('accord.workspace_id', :workspace, true)"),
        {"workspace": str(workspace)},
    )
    row = await session.scalar(
        select(PassportPublication)
        .where(PassportPublication.workspace_id == workspace, PassportPublication.id == publication)
        .with_for_update()
    )
    if row is None or await session.get(PassportUnpublication, publication) is not None:
        raise AccessDeniedError("public passport unavailable")
    if runtime is None:
        raise RuntimeError("public verification unavailable")
    package = SignedPassport.model_validate(row.package)
    if runtime.trust.verify(package) != "valid":
        raise RuntimeError("public issuance key is not trusted")
    public = PublicProjection.model_validate(package.payload)
    if (
        public.publication_id != row.id
        or set(public.values) != set(row.fields)
        or canonical(public.model_dump(mode="json")) != canonical(dict(package.payload))
    ):
        raise RuntimeError("public projection binding failed")
    issuance = await session.scalar(
        select(PassportIssuance).where(
            PassportIssuance.workspace_id == workspace, PassportIssuance.id == row.issuance_id
        )
    )
    if issuance is None:
        raise RuntimeError("public issuance unavailable")
    private = PassportPayload.model_validate(
        SignedPassport.model_validate(issuance.package).payload
    )
    if (
        private.version.workspace_id != workspace
        or public.version_revision != private.version.revision
        or public.valid_from != private.campaign.scope.starts_at
        or public.valid_until != private.campaign.scope.ends_at
    ):
        raise RuntimeError("public issuance binding failed")
    return row, public, private


def observed(session: AsyncSession, workspace: UUID, publication: UUID) -> None:
    session.add(
        Event(
            event_id=uuid4().hex,
            ts=datetime.now(UTC),
            actor_type="system",
            actor_id=None,
            tenant_id=workspace,
            category="persona",
            action="persona.publication_observed",
            outcome="success",
            severity="info",
            resource_type="public_passport",
            resource_id=str(publication),
            source="server",
            metadata_={},
        )
    )


async def inspect_public(
    session: AsyncSession,
    workspace: UUID,
    publication: UUID,
    runtime: PassportRuntime | None,
    uploaded: SignedPassport | None = None,
) -> PublicationPage:
    async with session.begin():
        row, _, payload = await approved_row(session, workspace, publication, runtime)
        saved = SignedPassport.model_validate(row.package)
        if runtime is None:
            raise RuntimeError("public verification unavailable")
        integrity = runtime.trust.verify(uploaded) if uploaded else "valid"
        if uploaded and integrity == "valid" and uploaded != saved:
            integrity = "binding_mismatch"
        current = "unavailable"
        if integrity == "valid":
            offer = await offer_row(session, workspace, payload.campaign.id)
            version, persona = await locked_version(session, workspace, offer.version_id)
            status = await current_status(session, offer, version, persona)
            current = (
                "eligible"
                if status.eligible_for_use
                and status.latest_decision is not None
                and status.latest_decision.id == payload.acceptance_id
                else "blocked"
            )
        observed(session, workspace, publication)
        result = PublicationPage(
            package=saved,
            verification=PublicVerification(
                integrity=integrity, current_use=current, evaluated_at=datetime.now(UTC)
            ),
        )
    return result


async def public_portrait(
    session: AsyncSession,
    workspace: UUID,
    publication: UUID,
    runtime: PassportRuntime | None,
    wrapper: KeyWrapper | None,
) -> bytes:
    async with session.begin():
        _, public, payload = await approved_row(session, workspace, publication, runtime)
        digest = public.values.get("portrait_sha256")
        if digest is None:
            raise AccessDeniedError("portrait was not approved for public visibility")
        photo = await primary_portrait(session, workspace, payload.version.version_id)
        if photo is None or photo.thumbnail_sha256 != digest or wrapper is None:
            raise RuntimeError("approved portrait unavailable")
        stored = await session.scalar(
            select(PortraitPayload).where(
                PortraitPayload.workspace_id == workspace,
                PortraitPayload.portrait_id == photo.id,
                PortraitPayload.part == "thumbnail",
            )
        )
        if stored is None:
            raise RuntimeError("approved portrait unavailable")
        async with asyncio.timeout(10):
            data = await decrypted_thumbnail(stored, photo, wrapper)
        observed(session, workspace, publication)
    return data
