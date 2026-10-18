"""Resolve an established binding; never provision accounts or grant roles during login."""

from uuid import UUID

from sqlalchemy import select, text

from accord.db.connection import _get_sessionmaker
from accord.personas.identity_models import IdentityBinding


async def resolve_identity(issuer: str, tenant: UUID, subject: UUID, workspace: UUID) -> str | None:
    async with _get_sessionmaker()() as session, session.begin():
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        result = await session.scalar(
            select(IdentityBinding.actor_ref).where(
                IdentityBinding.workspace_id == workspace,
                IdentityBinding.issuer == issuer,
                IdentityBinding.tenant_id == tenant,
                IdentityBinding.subject == subject,
            )
        )
        return result
