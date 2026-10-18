"""Append-only review decisions, including their exact request replay receipts."""

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


class ReviewRecord(Base):
    __tablename__ = "persona_reviews"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ordinal: Mapped[int] = mapped_column(nullable=False)
    reviewer_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    statement: Mapped[str] = mapped_column(String(500), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "version_id", "id"),
        UniqueConstraint("workspace_id", "reviewer_ref", "request_id"),
        UniqueConstraint("version_id", "ordinal"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["persona_versions.workspace_id", "persona_versions.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "reviewer_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("ordinal >= 1", name="ck_persona_reviews_ordinal"),
        CheckConstraint("decision IN ('approved', 'changes_requested')"),
        CheckConstraint("length(trim(statement)) > 0"),
    )
