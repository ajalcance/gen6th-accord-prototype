"""Owner/CI SQL proof: runtime may lock/read its member but cannot mutate grants."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.models import WorkspaceMember


async def test_read_function_preserves_tenant_scope_without_mutation_privilege(
    session: AsyncSession,
) -> None:
    workspace = uuid4()
    session.add(WorkspaceMember(workspace_id=workspace, actor_ref="member", role="creator"))
    await session.commit()
    async with session.begin():
        await session.execute(text("CREATE ROLE accord_lock_reader NOLOGIN"))
        await session.execute(text("GRANT USAGE ON SCHEMA public TO accord_lock_reader"))
        await session.execute(
            text(
                "GRANT EXECUTE ON FUNCTION accord_workspace_membership(UUID, VARCHAR) "
                "TO accord_lock_reader"
            )
        )
        await session.execute(text("SET LOCAL ROLE accord_lock_reader"))
        query = text("SELECT accord_workspace_membership(:w, 'member')")
        assert await session.scalar(query, {"w": workspace}) is None
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :w, true)"), {"w": str(workspace)}
        )
        assert await session.scalar(query, {"w": workspace}) == "creator"
        assert await session.scalar(query, {"w": uuid4()}) is None
        with pytest.raises(DBAPIError, match="permission denied"):
            async with session.begin_nested():
                await session.execute(text("UPDATE persona_workspace_members SET role = 'viewer'"))
        await session.execute(text("RESET ROLE"))
        await session.execute(
            text(
                "REVOKE EXECUTE ON FUNCTION accord_workspace_membership(UUID, VARCHAR) "
                "FROM accord_lock_reader"
            )
        )
        await session.execute(text("REVOKE USAGE ON SCHEMA public FROM accord_lock_reader"))
        await session.execute(text("DROP ROLE accord_lock_reader"))
