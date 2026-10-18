"""Capture inspected hashes for an attributed attestation; never decrypt or share originals."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.lifecycle_contracts import Dossier, Requirement
from accord.personas.repository import AccessDeniedError


def evidence_ids(dossier: Dossier, requirement: Requirement | None = None) -> set[UUID]:
    ids: set[UUID] = set()
    if requirement in (None, "operator"):
        ids.add(dossier.operator.evidence_id)
    if requirement in (None, "rights"):
        ids.update(right.evidence_id for right in dossier.rights)
    return ids


async def capture_digests(
    session: AsyncSession,
    workspace: UUID,
    version: UUID,
    owner: str,
    dossier: Dossier,
    requirement: Requirement | None = None,
) -> dict[str, str]:
    ids = evidence_ids(dossier, requirement)
    if not ids:
        return {}
    rows = await session.execute(
        select(PrivateEvidence.id, PrivateEvidence.sha256)
        .join(
            EvidenceInspection,
            (EvidenceInspection.workspace_id == PrivateEvidence.workspace_id)
            & (EvidenceInspection.evidence_id == PrivateEvidence.id),
        )
        .join(
            EvidencePayload,
            (EvidencePayload.workspace_id == PrivateEvidence.workspace_id)
            & (EvidencePayload.evidence_id == PrivateEvidence.id),
        )
        .where(
            PrivateEvidence.workspace_id == workspace,
            PrivateEvidence.version_id == version,
            PrivateEvidence.owner_ref == owner,
            PrivateEvidence.id.in_(ids),
            PrivateEvidence.expires_at > datetime.now(UTC),
            EvidenceInspection.verdict == "clean",
        )
        .with_for_update(of=PrivateEvidence)
    )
    digests = {str(key): digest for key, digest in rows}
    if set(digests) != {str(key) for key in ids}:
        raise AccessDeniedError(
            "lifecycle evidence must be owned, clean and available for this version"
        )
    return digests
