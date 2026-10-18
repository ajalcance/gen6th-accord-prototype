"""Queries require an authorized transaction; version locking serializes credit changes."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.credit_contracts import CreditConfirmation, CreditSnapshot
from accord.personas.credit_models import CreditAcceptance, CreditRecord
from accord.personas.repository import ConflictError


def snapshot(row: CreditRecord) -> CreditSnapshot:
    return CreditSnapshot.model_validate(
        {field: getattr(row, field) for field in CreditSnapshot.model_fields}
    )


def confirmation(row: CreditAcceptance) -> CreditConfirmation:
    return CreditConfirmation.model_validate(
        {field: getattr(row, field) for field in CreditConfirmation.model_fields}
    )


async def latest(session: AsyncSession, workspace: UUID, version: UUID) -> CreditRecord | None:
    rows = await session.scalars(
        select(CreditRecord)
        .where(CreditRecord.workspace_id == workspace, CreditRecord.version_id == version)
        .order_by(CreditRecord.ordinal.desc())
        .limit(1)
    )
    return rows.one_or_none()


async def confirmations(
    session: AsyncSession, workspace: UUID, profile: UUID
) -> tuple[CreditConfirmation, ...]:
    rows = await session.scalars(
        select(CreditAcceptance)
        .where(CreditAcceptance.workspace_id == workspace, CreditAcceptance.profile_id == profile)
        .order_by(CreditAcceptance.credit_index)
        .limit(12)
    )
    return tuple(confirmation(row) for row in rows)


async def replay[Record: CreditRecord | CreditAcceptance](
    session: AsyncSession,
    model: type[Record],
    workspace: UUID,
    actor: str,
    request_id: UUID,
    fingerprint: str,
) -> Record | None:
    actor_column = CreditRecord.declared_by if model is CreditRecord else CreditAcceptance.actor_ref
    row = await session.scalar(
        select(model).where(
            model.workspace_id == workspace, actor_column == actor, model.request_id == request_id
        )
    )
    if row is not None and row.fingerprint != fingerprint:
        raise ConflictError("credit request reused with different content")
    return row
