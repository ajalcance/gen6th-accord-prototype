"""Append-only credit declarations and confirmations, isolated from passport projections."""

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    String,
    Table,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base
from accord.personas.database_policy import execute_ddl, immutable_trigger, policies


class CreditRecord(Base):
    __tablename__ = "persona_credit_profiles"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ordinal: Mapped[int] = mapped_column(nullable=False)
    declared_by: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "declared_by", "request_id"),
        UniqueConstraint("workspace_id", "version_id", "ordinal"),
        UniqueConstraint("workspace_id", "version_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["persona_versions.workspace_id", "persona_versions.id"]
        ),
        CheckConstraint("ordinal >= 1 AND fingerprint ~ '^[0-9a-f]{64}$'"),
        CheckConstraint(
            "jsonb_typeof(content) = 'object' AND octet_length(content::text) <= 12000"
        ),
    )


class CreditAcceptance(Base):
    __tablename__ = "persona_credit_confirmations"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    profile_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    credit_index: Mapped[int] = mapped_column(nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "actor_ref", "request_id"),
        UniqueConstraint("workspace_id", "profile_id", "credit_index"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "profile_id"],
            [
                "persona_credit_profiles.workspace_id",
                "persona_credit_profiles.version_id",
                "persona_credit_profiles.id",
            ],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "actor_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("credit_index BETWEEN 0 AND 11 AND fingerprint ~ '^[0-9a-f]{64}$'"),
    )


def register_credit_policies() -> None:
    for model in (CreditRecord, CreditAcceptance):
        table = cast(Table, model.__table__)
        for statement in policies(table.name):
            event.listen(table, "after_create", execute_ddl(statement))
        event.listen(table, "after_create", execute_ddl(immutable_trigger(table.name)))
