"""Disposable SQL replay, signing concurrency and withdrawal; no live keys."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaigns import offer_campaign
from accord.personas.issuance_models import PassportIssuance, PassportPublication
from accord.personas.passport_service import export
from accord.personas.passport_signing import PassportRuntime
from accord.personas.publication_contracts import (
    ApprovePublication,
    PublicationHistoryQuery,
    PublicationReceipt,
)
from accord.personas.publication_history import history
from accord.personas.publication_reads import inspect_public
from accord.personas.publication_service import approve, unpublish
from accord.personas.repository import AccessDeniedError, ConflictError
from personas.campaign_fixtures import decision_intent
from personas.passport_fixtures import runtime
from personas.test_production_database import production_offer
from personas.workflow_fixtures import human


async def accepted(session: AsyncSession, workspace: UUID) -> ApprovePublication:
    _, offer = await production_offer(session, workspace)
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
    return ApprovePublication(
        request_id=uuid4(), campaign_id=offer.id, fields=("name", "ai_disclosure")
    )


async def test_public_grant_history_immutability_and_withdrawal(
    session: AsyncSession, workspace: UUID
) -> None:
    command, active = await accepted(session, workspace), runtime()
    receipt = await approve(session, workspace, human("creator-a"), command, active)
    assert await approve(session, workspace, human("creator-a"), command, active) == receipt
    page = await inspect_public(session, workspace, receipt.publication_id, active)
    assert page.verification.integrity == "valid" and page.verification.current_use == "eligible"
    values = page.package.payload["values"]
    assert isinstance(values, dict) and set(values) == {"name", "ai_disclosure"}
    with pytest.raises(AccessDeniedError):
        await inspect_public(session, uuid4(), receipt.publication_id, active)
    for model in (PassportIssuance, PassportPublication):
        with pytest.raises(DBAPIError, match="immutable"):
            async with session.begin():
                await session.execute(update(model).values(package={}))
    query = PublicationHistoryQuery(campaign_id=command.campaign_id)
    assert (await history(session, workspace, human("creator-a"), query)).items[
        0
    ].receipt == receipt
    assert (
        await unpublish(session, workspace, human("creator-a"), receipt.publication_id) == receipt
    )
    assert (
        await unpublish(session, workspace, human("creator-a"), receipt.publication_id) == receipt
    )
    assert (await history(session, workspace, human("creator-a"), query)).items[0].withdrawn
    with pytest.raises(AccessDeniedError):
        await inspect_public(session, workspace, receipt.publication_id, active)
    with pytest.raises(ConflictError, match="withdrawn"):
        await approve(session, workspace, human("creator-a"), command, active)


async def parallel_approval(
    engine: AsyncEngine, workspace: UUID, command: ApprovePublication, active: PassportRuntime
) -> PublicationReceipt:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        return await approve(session, workspace, human("creator-a"), command, active)


async def test_concurrent_approval_reuses_one_private_and_one_public_signature(
    db_engine: AsyncEngine, session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    command, active = await accepted(session, workspace), runtime()
    assert active.signer is not None
    signing = AsyncMock(wraps=active.signer.sign)
    monkeypatch.setattr(active.signer, "sign", signing)
    results = await asyncio.wait_for(
        asyncio.gather(
            parallel_approval(db_engine, workspace, command, active),
            parallel_approval(db_engine, workspace, command, active),
        ),
        timeout=10,
    )
    assert results[0] == results[1] and signing.await_count == 2
    assert await export(session, workspace, human("creator-a"), command.campaign_id, active)
    assert signing.await_count == 2
    assert await session.scalar(select(func.count()).select_from(PassportIssuance)) == 1
    assert await session.scalar(select(func.count()).select_from(PassportPublication)) == 1


@pytest.mark.parametrize("actor", ["reviewer-b", "creator-b", "viewer"])
async def test_recipient_and_other_members_cannot_approve_or_discover_public_grants(
    session: AsyncSession, workspace: UUID, actor: str
) -> None:
    command, active = await accepted(session, workspace), runtime()
    with pytest.raises(AccessDeniedError):
        await approve(session, workspace, human(actor), command, active)
    with pytest.raises(AccessDeniedError):
        await history(
            session,
            workspace,
            human(actor),
            PublicationHistoryQuery(campaign_id=command.campaign_id),
        )
    assert await session.scalar(select(func.count()).select_from(PassportPublication)) == 0


async def test_database_rejects_acceptance_from_a_different_campaign(
    session: AsyncSession, workspace: UUID
) -> None:
    use, original = await production_offer(session, workspace)
    other = await offer_campaign(
        session,
        workspace,
        human("creator-a"),
        use.model_copy(
            update={
                "request_id": uuid4(),
                "scope": use.scope.model_copy(update={"name": "Other scope"}),
            }
        ),
    )
    acceptance = await decide_campaign(
        session, workspace, human("reviewer-b"), decision_intent(other.id)
    )
    with pytest.raises(DBAPIError, match="foreign key"):
        async with session.begin():
            session.add(
                PassportIssuance(
                    id=uuid4(),
                    workspace_id=workspace,
                    campaign_id=original.id,
                    acceptance_id=acceptance.id,
                    package={},
                    recorded_at=datetime.now(UTC),
                )
            )
