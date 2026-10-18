"""Metadata-created campaign protections; migration 0005 freezes equivalent SQL."""

from typing import cast

from sqlalchemy import Table, event

from accord.personas.campaign_models import (
    CampaignAsset,
    CampaignDecision,
    CampaignOffer,
    PersonaAsset,
)
from accord.personas.database_policy import execute_ddl, immutable_trigger, policies

CAMPAIGN_TABLES: tuple[Table, ...] = tuple(
    cast(Table, model.__table__)
    for model in (
        PersonaAsset,
        CampaignOffer,
        CampaignAsset,
        CampaignDecision,
    )
)


def register_campaign_policies() -> None:
    for table in CAMPAIGN_TABLES:
        for statement in (*policies(table.name), immutable_trigger(table.name)):
            event.listen(table, "after_create", execute_ddl(statement))
