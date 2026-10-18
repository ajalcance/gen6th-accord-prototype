"""Exact-version, owner-scoped inspection checks; no private evidence disclosure."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.production_contracts import ProductionUse
from accord.personas.repository import AccessDeniedError


async def supporting_evidence_available(
    session: AsyncSession,
    workspace: UUID,
    version: UUID,
    owner: str,
    production: ProductionUse | None,
) -> bool:
    if production is None or not production.supporting_references:
        return True
    ids = {item.evidence_id for item in production.supporting_references}
    rows = await session.scalars(
        select(PrivateEvidence.id)
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
        .limit(9)
    )
    return set(rows) == ids


async def require_supporting_evidence(
    session: AsyncSession,
    workspace: UUID,
    version: UUID,
    owner: str,
    production: ProductionUse | None,
) -> None:
    if not await supporting_evidence_available(session, workspace, version, owner, production):
        raise AccessDeniedError("supporting evidence is unavailable for this exact version")
