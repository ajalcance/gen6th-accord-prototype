"""Immutable asset bindings, campaign offers and decision histories."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class PersonaAsset(Base):
    """Server-managed assets, enrolled explicitly from inspected exact-version evidence."""

    __tablename__ = "persona_assets"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "version_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["persona_versions.workspace_id", "persona_versions.id"]
        ),
        CheckConstraint("length(trim(label)) > 0", name="ck_persona_assets_label"),
        CheckConstraint("digest ~ '^[0-9a-f]{64}$'"),
    )


class CampaignOffer(Base):
    __tablename__ = "persona_campaign_offers"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    review_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    purpose: Mapped[str] = mapped_column(String(500), nullable=False)
    conditions: Mapped[str] = mapped_column(String(500), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    production: Mapped[dict[str, object] | None] = mapped_column(
        JSONB(none_as_null=True), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "version_id", "id"),
        UniqueConstraint("workspace_id", "owner_ref", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "review_id"],
            ["persona_reviews.workspace_id", "persona_reviews.version_id", "persona_reviews.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "owner_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "recipient_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("owner_ref <> recipient_ref", name="ck_persona_campaign_parties"),
        CheckConstraint("ends_at > starts_at AND ends_at <= starts_at + interval '366 days'"),
        CheckConstraint(
            "production IS NULL OR (jsonb_typeof(production) = 'object' "
            "AND octet_length(production::text) <= 8192)",
            name="ck_campaign_production_bound",
        ),
        CheckConstraint(
            "length(trim(name)) > 0 AND length(trim(purpose)) > 0 AND length(trim(conditions)) > 0"
        ),
    )


class CampaignAsset(Base):
    __tablename__ = "persona_campaign_assets"
    workspace_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "campaign_id"],
            [
                "persona_campaign_offers.workspace_id",
                "persona_campaign_offers.version_id",
                "persona_campaign_offers.id",
            ],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "asset_id"],
            [
                "persona_assets.workspace_id",
                "persona_assets.version_id",
                "persona_assets.id",
            ],
        ),
    )


class CampaignDecision(Base):
    __tablename__ = "persona_campaign_decisions"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ordinal: Mapped[int] = mapped_column(nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    statement: Mapped[str] = mapped_column(String(500), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "actor_ref", "request_id"),
        UniqueConstraint("campaign_id", "ordinal"),
        UniqueConstraint("workspace_id", "campaign_id", "id", name="uq_campaign_decision_scope"),
        ForeignKeyConstraint(
            ["workspace_id", "campaign_id"],
            ["persona_campaign_offers.workspace_id", "persona_campaign_offers.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "actor_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("ordinal >= 1", name="ck_persona_campaign_ordinal"),
        CheckConstraint("decision IN ('accepted', 'changes_requested', 'revoked')"),
        CheckConstraint("length(trim(statement)) > 0"),
    )
