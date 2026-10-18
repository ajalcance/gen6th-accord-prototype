"""Immutable replay records; permission checks remain in the owning service transaction."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import CampaignStatus
from accord.personas.capture_reads import reference_captures
from accord.personas.issuance_models import PassportIssuance
from accord.personas.models import Version
from accord.personas.passport_contracts import PassportPayload, SignedPassport
from accord.personas.passport_signing import PassportRuntime
from accord.personas.repository import ConflictError, snapshot
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event


async def stored_issuance(
    session: AsyncSession, workspace: UUID, campaign: UUID, acceptance: UUID
) -> SignedPassport | None:
    row = await session.scalar(
        select(PassportIssuance).where(
            PassportIssuance.workspace_id == workspace,
            PassportIssuance.campaign_id == campaign,
            PassportIssuance.acceptance_id == acceptance,
        )
    )
    return SignedPassport.model_validate(row.package) if row else None


def remember_issuance(
    session: AsyncSession,
    workspace: UUID,
    actor: WorkflowActor,
    payload: PassportPayload,
    package: SignedPassport,
) -> None:
    record_id = uuid4()
    session.add(
        PassportIssuance(
            id=record_id,
            workspace_id=workspace,
            campaign_id=payload.campaign.id,
            acceptance_id=payload.acceptance_id,
            package=package.model_dump(mode="json"),
            recorded_at=payload.issued_at,
        )
    )

    session.add(
        decision_event(
            workspace_id=workspace,
            actor_ref=actor.actor_ref,
            request_id=uuid4(),
            record_id=record_id,
            version_id=payload.version.version_id,
            event_id=uuid4().hex,
            recorded_at=payload.issued_at,
            action="persona.passport_issued",
        )
    )


async def validate_replay(
    session: AsyncSession,
    workspace: UUID,
    version: Version,
    status: CampaignStatus,
    package: SignedPassport,
    runtime: PassportRuntime,
) -> None:
    if runtime.trust.verify(package) != "valid":
        raise RuntimeError("retained issuance key is not trusted")
    old = PassportPayload.model_validate(package.payload)
    references = await reference_captures(session, workspace, version.id)
    if (
        old.version != snapshot(version)
        or old.campaign != status.receipt
        or old.references != references
    ):
        raise ConflictError("persisted issuance bindings changed")
