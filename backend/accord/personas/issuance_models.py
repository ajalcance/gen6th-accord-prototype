"""Persisted private issuances and separately approved public projections/revocations."""

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


class PassportIssuance(Base):
    __tablename__ = "persona_passport_issuances"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    acceptance_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    package: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "campaign_id", "acceptance_id"),
        ForeignKeyConstraint(
            ["workspace_id", "campaign_id"],
            ["persona_campaign_offers.workspace_id", "persona_campaign_offers.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "campaign_id", "acceptance_id"],
            [
                "persona_campaign_decisions.workspace_id",
                "persona_campaign_decisions.campaign_id",
                "persona_campaign_decisions.id",
            ],
        ),
        CheckConstraint(
            "jsonb_typeof(package) = 'object' AND octet_length(package::text) <= 131072"
        ),
    )


class PassportPublication(Base):
    __tablename__ = "persona_passport_publications"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    issuance_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    package: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "owner_ref", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "issuance_id"],
            ["persona_passport_issuances.workspace_id", "persona_passport_issuances.id"],
        ),
        CheckConstraint(
            "jsonb_typeof(fields) = 'array' AND jsonb_array_length(fields) BETWEEN 2 AND 8"
        ),
        CheckConstraint(
            "jsonb_typeof(package) = 'object' AND octet_length(package::text) <= 16384"
        ),
    )


class PassportUnpublication(Base):
    __tablename__ = "persona_passport_unpublications"
    publication_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "publication_id"],
            ["persona_passport_publications.workspace_id", "persona_passport_publications.id"],
        ),
    )
