"""Server-seeded synthetic asset references and named fixture campaign intents."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.campaign_contracts import (
    CampaignDecisionCommand,
    CampaignScope,
    OfferCampaignCommand,
)
from accord.personas.campaign_models import PersonaAsset
from accord.personas.contracts import PersonaVersion
from accord.personas.reviews import record_review
from accord.personas.workflow_contracts import ReviewSnapshot
from personas.workflow_fixtures import draft_for_review, human, review_intent


async def campaign_material(
    session: AsyncSession, workspace: UUID
) -> tuple[PersonaVersion, ReviewSnapshot, tuple[UUID, ...]]:
    version = await draft_for_review(session, workspace)
    review = await record_review(
        session, workspace, human("reviewer-a"), review_intent(version.version_id)
    )
    ids = tuple(sorted((uuid4(), uuid4()), key=str))
    session.add_all(
        [
            PersonaAsset(
                id=asset_id,
                workspace_id=workspace,
                version_id=version.version_id,
                digest=hashlib.sha256(
                    f"Original fictional illustration {index}".encode()
                ).hexdigest(),
                label=f"Fictional illustration {index}",
            )
            for index, asset_id in enumerate(ids)
        ]
    )
    await session.commit()
    return version, review, ids


def campaign_scope(target_asset_ids: tuple[UUID, ...], **changes: object) -> CampaignScope:
    now = datetime.now(UTC)
    return CampaignScope.model_validate(
        {
            "name": "Fictional North campaign",
            "recipient_ref": "reviewer-b",
            "asset_ids": target_asset_ids,
            "purpose": "Fictional editorial campaign only.",
            "conditions": "No sublicensing; fictional fixture.",
            "starts_at": now - timedelta(hours=1),
            "ends_at": now + timedelta(days=30),
            **changes,
        }
    )


def offer_intent(
    version_id: UUID, review_id: UUID, asset_ids: tuple[UUID, ...], **changes: object
) -> OfferCampaignCommand:
    return OfferCampaignCommand.model_validate(
        {
            "request_id": uuid4(),
            "version_id": version_id,
            "review_id": review_id,
            "scope": campaign_scope(asset_ids),
            **changes,
        }
    )


def decision_intent(target_campaign_id: UUID, **changes: object) -> CampaignDecisionCommand:
    return CampaignDecisionCommand.model_validate(
        {
            "request_id": uuid4(),
            "campaign_id": target_campaign_id,
            "decision": "accepted",
            "statement": "Recipient accepts the specified fictional scope.",
            **changes,
        }
    )
