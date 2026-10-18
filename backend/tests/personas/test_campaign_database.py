"""Immutable campaign storage and composite asset/version boundaries on PostgreSQL."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import JSON, Table, func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_decisions import decide_campaign
from accord.personas.campaign_models import (
    CampaignAsset,
    CampaignDecision,
    CampaignOffer,
    PersonaAsset,
)
from accord.personas.campaign_policy import CAMPAIGN_TABLES
from accord.personas.campaigns import offer_campaign
from accord.personas.service import save
from personas.campaign_fixtures import campaign_material, decision_intent, offer_intent
from personas.conftest import command
from personas.workflow_fixtures import human


@pytest.mark.parametrize("table_index", range(len(CAMPAIGN_TABLES)))
@pytest.mark.parametrize("operation", ["update", "delete"])
async def test_metadata_campaign_records_are_immutable(
    session: AsyncSession, workspace: UUID, table_index: int, operation: str
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
    with pytest.raises(DBAPIError, match="immutable"):
        async with session.begin():
            table = CAMPAIGN_TABLES[table_index]
            await session.execute(
                table.delete()
                if operation == "delete"
                else table.update().values(workspace_id=workspace)
            )


async def test_metadata_campaign_rls_scopes_every_table(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
    async with session.begin():
        await session.execute(text("SET LOCAL ROLE pg_read_all_data"))
        for table in CAMPAIGN_TABLES:
            assert await session.scalar(select(func.count()).select_from(table)) == 0
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
        )
        for table in CAMPAIGN_TABLES:
            assert await session.scalar(select(func.count()).select_from(table)) == 0
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        for table, expected in zip(CAMPAIGN_TABLES, (2, 1, 2, 1), strict=True):
            assert await session.scalar(select(func.count()).select_from(table)) == expected


async def test_db_cannot_bind_assets_from_another_version(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    other = await save(session, workspace, "creator-b", command())
    asset = uuid4()
    session.add(
        PersonaAsset(
            id=asset,
            workspace_id=workspace,
            version_id=other.version_id,
            digest="a" * 64,
            label="Other fictional portrait",
        )
    )
    await session.commit()
    with pytest.raises(IntegrityError, match="persona_assets"):
        async with session.begin():
            session.add(
                CampaignAsset(
                    workspace_id=workspace,
                    campaign_id=offer.id,
                    version_id=version.version_id,
                    asset_id=asset,
                )
            )
            await session.flush()


async def test_db_cannot_duplicate_decision_ordinal(session: AsyncSession, workspace: UUID) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    await decide_campaign(session, workspace, human("reviewer-b"), decision_intent(offer.id))
    with pytest.raises(IntegrityError, match="unique"):
        async with session.begin():
            await session.execute(
                cast(Table, CampaignDecision.__table__)
                .insert()
                .values(
                    id=uuid4(),
                    workspace_id=workspace,
                    campaign_id=offer.id,
                    ordinal=1,
                    actor_ref="reviewer-b",
                    request_id=uuid4(),
                    fingerprint="a" * 64,
                    decision="accepted",
                    statement="Duplicate fictional acceptance",
                    recorded_at=datetime.now(UTC),
                    event_id=uuid4().hex,
                )
            )


async def test_absent_production_is_sql_null_and_json_null_is_rejected(
    session: AsyncSession, workspace: UUID
) -> None:
    version, review, ids = await campaign_material(session, workspace)
    offer = await offer_campaign(
        session, workspace, human("creator-a"), offer_intent(version.version_id, review.id, ids)
    )
    async with session.begin():
        row = await session.get(CampaignOffer, offer.id)
        assert row is not None and row.production is None
        assert await session.scalar(
            select(CampaignOffer.production.is_(None)).where(CampaignOffer.id == offer.id)
        )
        table = cast(Table, CampaignOffer.__table__)
        values = {column.key: getattr(row, column.key) for column in table.columns}
        values.update(id=uuid4(), request_id=uuid4(), event_id=uuid4().hex, production=JSON.NULL)
        with pytest.raises(IntegrityError, match="ck_campaign_production_bound"):
            async with session.begin_nested():
                await session.execute(table.insert().values(**values))
