"""Two PostgreSQL workers cannot fork the audit chain, including at genesis."""

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.command.audit import seal_new, verify_chain
from accord.personas.service import save
from personas.conftest import command


async def test_concurrent_sealers_share_one_chain(
    session: AsyncSession, db_engine: AsyncEngine, workspace: UUID
) -> None:
    await save(session, workspace, "creator-a", command())
    await save(session, workspace, "creator-b", command("Fictional Iris"))
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def seal() -> int:
        async with maker() as worker_session:
            return await seal_new(worker_session)

    counts = await asyncio.wait_for(asyncio.gather(seal(), seal()), timeout=10)
    assert sorted(counts) == [0, 2]
    assert await verify_chain(session) == (True, None, 2)
    await session.rollback()
    counts = await asyncio.wait_for(asyncio.gather(seal(), seal()), timeout=10)
    assert sorted(counts) == [0, 0]
