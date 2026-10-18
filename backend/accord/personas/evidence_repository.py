"""Tenant/owner queries and metadata projection for private evidence."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.evidence_contracts import EvidenceSnapshot, effective_state
from accord.personas.evidence_crypto import KeyWrapper, SealedEvidence, binding, unseal
from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.repository import AccessDeniedError
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor


async def owned(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    evidence_id: UUID,
    *,
    lock: bool = True,
) -> PrivateEvidence:
    await authorize_actor(session, workspace_id, actor, "creator")
    query = (
        select(PrivateEvidence)
        .where(
            PrivateEvidence.workspace_id == workspace_id,
            PrivateEvidence.owner_ref == actor.actor_ref,
            PrivateEvidence.id == evidence_id,
        )
        .execution_options(populate_existing=True)
    )
    row = await session.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise AccessDeniedError("private evidence access denied")
    return row


def snapshot(row: PrivateEvidence, verdict: str | None = None) -> EvidenceSnapshot:
    return EvidenceSnapshot.model_validate(
        {
            "id": row.id,
            "workspace_id": row.workspace_id,
            "version_id": row.version_id,
            "media_type": row.media_type,
            "byte_length": row.byte_length,
            "sha256": row.sha256,
            "recorded_at": row.recorded_at,
            "expires_at": row.expires_at,
            "state": effective_state(row.expires_at, datetime.now(UTC), verdict),
        }
    )


def observed(
    row: PrivateEvidence,
    actor: WorkflowActor,
    request_id: UUID,
    action: str,
    verdict: str | None = None,
) -> Event:
    return Event(
        event_id=uuid4().hex,
        ts=datetime.now(UTC),
        actor_type=actor.audit_type,
        actor_id=actor.actor_ref,
        tenant_id=row.workspace_id,
        category="persona",
        action=action,
        outcome="success",
        severity="info",
        resource_type="private_evidence",
        resource_id=str(row.id),
        correlation_id=str(request_id),
        source="server",
        metadata_={"version_id": str(row.version_id), "state": snapshot(row, verdict).state},
    )


async def inspection(session: AsyncSession, row: PrivateEvidence) -> EvidenceInspection | None:
    rows = await session.scalars(
        select(EvidenceInspection).where(
            EvidenceInspection.workspace_id == row.workspace_id,
            EvidenceInspection.evidence_id == row.id,
        )
    )
    return rows.one_or_none()


async def payload(session: AsyncSession, row: PrivateEvidence) -> EvidencePayload | None:
    rows = await session.scalars(
        select(EvidencePayload).where(
            EvidencePayload.workspace_id == row.workspace_id,
            EvidencePayload.evidence_id == row.id,
        )
    )
    return rows.one_or_none()


async def plaintext(session: AsyncSession, row: PrivateEvidence, wrapper: KeyWrapper) -> bytes:
    stored = await payload(session, row)
    if stored is None or datetime.now(UTC) >= row.expires_at:
        raise AccessDeniedError("private evidence is unavailable")
    sealed = SealedEvidence(stored.ciphertext, stored.nonce, stored.key_id, stored.wrapped_key)
    context = binding(row.workspace_id, row.version_id, row.id, row.sha256)
    return await unseal(sealed, context, wrapper)
