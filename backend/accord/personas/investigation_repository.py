"""Workspace/version-bound history and replay; caller holds the persona serialization lock."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.investigation_contracts import InvestigationCommand, InvestigationHistory
from accord.personas.investigation_models import InvestigationRecord
from accord.personas.investigation_storage import intent_fingerprint
from accord.personas.repository import ConflictError


async def replay(
    session: AsyncSession, workspace: UUID, actor: str, command: InvestigationCommand
) -> InvestigationRecord | None:
    row = await session.scalar(
        select(InvestigationRecord).where(
            InvestigationRecord.workspace_id == workspace,
            InvestigationRecord.actor_ref == actor,
            InvestigationRecord.request_id == command.request_id,
        )
    )
    if row is not None and row.fingerprint != intent_fingerprint(command):
        raise ConflictError("investigation request reused with different intent")
    return row


async def history(
    session: AsyncSession, workspace: UUID, command: InvestigationHistory
) -> list[InvestigationRecord]:
    statement = select(InvestigationRecord).where(
        InvestigationRecord.workspace_id == workspace,
        InvestigationRecord.version_id == command.version_id,
    )
    if command.before_ordinal is not None:
        statement = statement.where(InvestigationRecord.ordinal < command.before_ordinal)
    return list(
        await session.scalars(statement.order_by(InvestigationRecord.ordinal.desc()).limit(21))
    )
