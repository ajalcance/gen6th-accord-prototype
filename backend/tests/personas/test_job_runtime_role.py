"""Prepared disposable-SQL runtime proof; never grant privileges to the real application role."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_repository import reference
from accord.personas.job_models import FaceJob
from accord.personas.job_repository import job_lock, latest, transition
from accord.personas.job_service import enqueue
from personas.test_job_database import setup_job
from personas.workflow_fixtures import human

TABLES = (
    "persona_face_jobs",
    "persona_face_job_transitions",
    "persona_face_generations",
    "persona_portraits",
    "persona_portrait_captures",
    "persona_version_references",
    "persona_versions",
    "personas",
)


async def create_role(session: AsyncSession) -> None:
    await session.execute(text("CREATE ROLE accord_job_reader NOLOGIN"))
    await session.execute(text("GRANT USAGE ON SCHEMA public TO accord_job_reader"))
    for table in TABLES:
        await session.execute(text(f"GRANT SELECT ON {table} TO accord_job_reader"))
    await session.execute(text("GRANT INSERT ON persona_face_job_transitions TO accord_job_reader"))
    await session.execute(text("GRANT UPDATE ON personas TO accord_job_reader"))
    await session.execute(text("SET LOCAL ROLE accord_job_reader"))


async def drop_role(session: AsyncSession) -> None:
    await session.execute(text("RESET ROLE"))
    for table in TABLES:
        await session.execute(text(f"REVOKE ALL ON {table} FROM accord_job_reader"))
    await session.execute(text("REVOKE USAGE ON SCHEMA public FROM accord_job_reader"))
    await session.execute(text("DROP ROLE accord_job_reader"))


@pytest.mark.asyncio
async def test_runtime_tenant_isolation_and_locking_need_no_portrait_update(
    session: AsyncSession, workspace: UUID
) -> None:
    intent, runtime = await setup_job(session, workspace)
    await enqueue(session, workspace, human("creator-a"), intent, runtime)
    async with session.begin():
        await create_role(session)
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :scope, true)"), {"scope": str(uuid4())}
        )
        assert await session.scalar(select(func.count()).select_from(FaceJob)) == 0
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :scope, true)"),
            {"scope": str(workspace)},
        )
        assert await session.scalar(select(func.count()).select_from(FaceJob)) == 1
        await job_lock(session, workspace, intent.request_id, wait=False)
        await reference(session, workspace, "creator-a", intent, write=True)
        row = await session.get(FaceJob, intent.request_id)
        assert row is not None
        transition(session, row, await latest(session, row), "cancelled")
        await session.flush()
        with pytest.raises(DBAPIError, match="permission denied"):
            async with session.begin_nested():
                await session.execute(text("UPDATE persona_portraits SET media_type = 'image/png'"))
        await drop_role(session)
