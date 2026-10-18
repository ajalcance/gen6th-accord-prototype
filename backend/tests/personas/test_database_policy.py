"""Real PostgreSQL enforcement, including a role without superuser/BYPASSRLS."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.models import Persona, Version, WriteReceipt
from accord.personas.service import save
from personas.conftest import command


@pytest.mark.parametrize("table", [Version, WriteReceipt])
@pytest.mark.parametrize("operation", ["update", "delete"])
async def test_record_cannot_be_mutated(
    session: AsyncSession,
    workspace: UUID,
    table: type[Version] | type[WriteReceipt],
    operation: str,
) -> None:
    await save(session, workspace, "creator-a", command())
    with pytest.raises(DBAPIError, match="immutable"):
        async with session.begin():
            statement = (
                delete(table)
                if operation == "delete"
                else update(table).values(workspace_id=workspace)
            )
            await session.execute(statement)


async def test_rls_missing_and_other_workspace_are_denied(
    session: AsyncSession,
    workspace: UUID,
) -> None:
    first = await save(session, workspace, "creator-a", command())
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
        assert list(await session.scalars(select(Persona))) == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
        )
        assert list(await session.scalars(select(Version))) == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        rows = list(await session.scalars(select(Version)))
        assert [row.id for row in rows] == [first.version_id]
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
        assert list(await session.scalars(select(Version))) == []


async def test_rls_refuses_cross_workspace_insert(session: AsyncSession, workspace: UUID) -> None:
    with pytest.raises(DBAPIError, match="row-level security"):
        async with session.begin():
            await session.execute(text("SET LOCAL ROLE pg_write_all_data"))
            await session.execute(
                text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
            )
            session.add(
                Persona(id=uuid4(), workspace_id=uuid4(), owner_ref="creator-a", head_revision=1)
            )
            await session.flush()


async def test_version_has_only_one_write_receipt(session: AsyncSession, workspace: UUID) -> None:
    first = await save(session, workspace, "creator-a", command())
    with pytest.raises(IntegrityError, match="unique"):
        async with session.begin():
            session.add(
                WriteReceipt(
                    workspace_id=workspace,
                    actor_ref="creator-a",
                    request_id=uuid4(),
                    fingerprint="a" * 64,
                    version_id=first.version_id,
                )
            )
            await session.flush()
