"""Append-only exact-version requests linked to a saved investigation."""

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


class InvestigationReviewRequest(Base):
    __tablename__ = "persona_investigation_review_requests"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    investigation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ordinal: Mapped[int] = mapped_column(nullable=False)
    requester_ref: Mapped[str] = mapped_column(String(160), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "requester_ref", "request_id"),
        UniqueConstraint("workspace_id", "version_id", "ordinal"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "investigation_id"],
            [
                "persona_investigations.workspace_id",
                "persona_investigations.version_id",
                "persona_investigations.id",
            ],
        ),
        CheckConstraint("ordinal >= 1 AND length(requester_ref) > 0"),
    )
