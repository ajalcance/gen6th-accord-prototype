"""Tenant-scoped record persistence; no private evidence or identity credentials."""

from __future__ import annotations

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
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class WorkspaceMember(Base):
    """Server-managed membership. No registration or browser grant path exists."""

    __tablename__ = "persona_workspace_members"
    workspace_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    actor_ref: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(16))
    __table_args__ = (CheckConstraint("role IN ('creator', 'reviewer', 'viewer')"),)


class Persona(Base):
    """Mutable head pointer to an append-only creation history."""

    __tablename__ = "personas"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    head_revision: Mapped[int] = mapped_column(nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "owner_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("head_revision >= 1"),
    )


class Version(Base):
    """Database-protected immutable content, provenance and server receipt time."""

    __tablename__ = "persona_versions"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    persona_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False)
    creator_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    biography: Mapped[str] = mapped_column(String(500), nullable=False)
    human_contribution: Mapped[str] = mapped_column(String(500), nullable=False)
    ai_disclosure: Mapped[str] = mapped_column(String(500), nullable=False)
    # The cold event store expires; the audit chain retains the same event identifier.
    event_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "persona_id"],
            ["personas.workspace_id", "personas.id"],
        ),
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("persona_id", "revision"),
        UniqueConstraint("workspace_id", "persona_id", "id", name="uq_version_lifecycle_binding"),
        CheckConstraint("revision >= 1", name="ck_persona_versions_revision"),
        CheckConstraint("length(trim(name)) > 0 AND length(trim(biography)) > 0"),
        CheckConstraint("length(trim(human_contribution)) > 0 AND length(trim(ai_disclosure)) > 0"),
    )


class WriteReceipt(Base):
    """Exact request replay receipt; mismatched re-use is rejected."""

    __tablename__ = "persona_write_receipts"
    workspace_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    actor_ref: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    __table_args__ = (
        UniqueConstraint("version_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["persona_versions.workspace_id", "persona_versions.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "actor_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
    )
