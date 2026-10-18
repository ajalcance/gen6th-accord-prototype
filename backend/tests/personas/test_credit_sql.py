"""Run only on disposable PostgreSQL: actual persistence, RLS and immutable history."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas import credit_service as credits
from accord.personas.credit_contracts import (
    ConfirmCredit,
    Credit,
    CreditContent,
    CreditSubject,
    SaveCredits,
)
from accord.personas.credit_models import CreditAcceptance, CreditRecord
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from personas.conftest import command
from personas.workflow_fixtures import human


async def declared(session: AsyncSession, workspace: UUID) -> SaveCredits:
    version = await save(session, workspace, "creator-a", command())
    return SaveCredits(
        request_id=uuid4(),
        version_id=version.version_id,
        content=CreditContent(
            aliases=("Nova",),
            credits=(Credit(name="Contributor", kind="human", role="design", actor_ref="viewer"),),
        ),
    )


async def test_owner_declaration_and_self_confirmation_replay_and_replacement(
    session: AsyncSession, workspace: UUID
) -> None:
    intent = await declared(session, workspace)
    profile = await credits.save(session, workspace, human("creator-a"), intent)
    assert await credits.save(session, workspace, human("creator-a"), intent) == profile
    confirm = ConfirmCredit(
        request_id=uuid4(), version_id=intent.version_id, profile_id=profile.id, credit_index=0
    )
    with pytest.raises(AccessDeniedError):
        await credits.confirm(session, workspace, human("creator-a"), confirm)
    accepted = await credits.confirm(session, workspace, human("viewer"), confirm)
    assert await credits.confirm(session, workspace, human("viewer"), confirm) == accepted
    replacement = await credits.save(
        session,
        workspace,
        human("creator-a"),
        intent.model_copy(update={"request_id": uuid4(), "expected_previous_id": profile.id}),
    )
    read = await credits.read(
        session, workspace, human("viewer"), CreditSubject(version_id=intent.version_id)
    )
    assert read.snapshot == replacement and not read.confirmations
    with pytest.raises(ConflictError):
        await credits.confirm(
            session, workspace, human("viewer"), confirm.model_copy(update={"request_id": uuid4()})
        )


@pytest.mark.parametrize("actor", ["creator-b", "viewer"])
async def test_nonowners_cannot_declare(session: AsyncSession, workspace: UUID, actor: str) -> None:
    intent = await declared(session, workspace)
    with pytest.raises(AccessDeniedError):
        await credits.save(session, workspace, human(actor), intent)
    assert await session.scalar(select(CreditRecord.id)) is None


@pytest.mark.parametrize("model", [CreditRecord, CreditAcceptance])
async def test_database_blocks_mutation(
    session: AsyncSession, workspace: UUID, model: type[CreditRecord] | type[CreditAcceptance]
) -> None:
    intent = await declared(session, workspace)
    profile = await credits.save(session, workspace, human("creator-a"), intent)
    await credits.confirm(
        session,
        workspace,
        human("viewer"),
        ConfirmCredit(
            request_id=uuid4(), version_id=intent.version_id, profile_id=profile.id, credit_index=0
        ),
    )
    with pytest.raises(DBAPIError, match="immutable"):
        await session.execute(update(model).values(workspace_id=workspace))
    await session.rollback()


async def test_rls_hides_foreign_and_unscoped_credits(
    session: AsyncSession, workspace: UUID
) -> None:
    intent = await declared(session, workspace)
    await credits.save(session, workspace, human("creator-a"), intent)
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
        assert (await session.scalars(select(CreditRecord))).all() == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :w, true)"), {"w": str(uuid4())}
        )
        assert (await session.scalars(select(CreditRecord))).all() == []
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :w, true)"), {"w": str(workspace)}
        )
        assert len((await session.scalars(select(CreditRecord))).all()) == 1
