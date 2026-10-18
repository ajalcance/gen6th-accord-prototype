"""Scoped immutable campaign reads; callers own authorization and transactions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import (
    AssetSnapshot,
    CampaignDecisionReceipt,
    CampaignReceipt,
    CampaignScope,
)
from accord.personas.campaign_models import (
    CampaignAsset,
    CampaignDecision,
    CampaignOffer,
    PersonaAsset,
)
from accord.personas.production_contracts import ProductionUse
from accord.personas.repository import AccessDeniedError


async def offer_row(session: AsyncSession, workspace_id: UUID, campaign_id: UUID) -> CampaignOffer:
    row = await session.scalar(
        select(CampaignOffer).where(
            CampaignOffer.workspace_id == workspace_id,
            CampaignOffer.id == campaign_id,
        )
    )
    if row is None:
        raise AccessDeniedError("campaign access denied")
    return row


async def scoped_assets(
    session: AsyncSession, workspace_id: UUID, version_id: UUID, asset_ids: tuple[UUID, ...]
) -> tuple[PersonaAsset, ...]:
    rows = tuple(
        await session.scalars(
            select(PersonaAsset)
            .where(
                PersonaAsset.workspace_id == workspace_id,
                PersonaAsset.version_id == version_id,
                PersonaAsset.id.in_(asset_ids),
            )
            .order_by(PersonaAsset.id)
        )
    )
    if tuple(row.id for row in rows) != asset_ids:
        raise AccessDeniedError("campaign assets are not authorized for this version")
    return rows


async def campaign_receipt(session: AsyncSession, row: CampaignOffer) -> CampaignReceipt:
    bindings = tuple(
        await session.scalars(
            select(CampaignAsset.asset_id)
            .where(
                CampaignAsset.workspace_id == row.workspace_id,
                CampaignAsset.campaign_id == row.id,
                CampaignAsset.version_id == row.version_id,
            )
            .order_by(CampaignAsset.asset_id)
        )
    )
    assets = await scoped_assets(session, row.workspace_id, row.version_id, bindings)
    scope = CampaignScope(
        name=row.name,
        recipient_ref=row.recipient_ref,
        asset_ids=bindings,
        purpose=row.purpose,
        conditions=row.conditions,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        production=(
            ProductionUse.model_validate(row.production) if row.production is not None else None
        ),
    )
    return CampaignReceipt(
        id=row.id,
        workspace_id=row.workspace_id,
        version_id=row.version_id,
        review_id=row.review_id,
        owner_ref=row.owner_ref,
        scope=scope,
        recorded_at=row.recorded_at,
        event_id=row.event_id,
        assets=tuple(
            AssetSnapshot(id=asset.id, digest=asset.digest, label=asset.label) for asset in assets
        ),
    )


async def latest_campaign_decision(
    session: AsyncSession, workspace_id: UUID, campaign_id: UUID
) -> CampaignDecision | None:
    rows = await session.scalars(
        select(CampaignDecision)
        .where(
            CampaignDecision.workspace_id == workspace_id,
            CampaignDecision.campaign_id == campaign_id,
        )
        .order_by(CampaignDecision.ordinal.desc())
        .limit(1)
    )
    return rows.one_or_none()


def decision_receipt(row: CampaignDecision) -> CampaignDecisionReceipt:
    return CampaignDecisionReceipt.model_validate(
        {field: getattr(row, field) for field in CampaignDecisionReceipt.model_fields}
    )
