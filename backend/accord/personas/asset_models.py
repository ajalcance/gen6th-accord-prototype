"""Immutable provenance for explicitly enrolled production assets."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKeyConstraint, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class AssetEnrollment(Base):
    __tablename__ = "persona_asset_enrollments"
    asset_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    evidence_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    permission_statement: Mapped[str] = mapped_column(String(500), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "owner_ref", "request_id"),
        UniqueConstraint("workspace_id", "version_id", "evidence_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "asset_id"],
            ["persona_assets.workspace_id", "persona_assets.version_id", "persona_assets.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "evidence_id"],
            [
                "persona_private_evidence.workspace_id",
                "persona_private_evidence.version_id",
                "persona_private_evidence.id",
            ],
        ),
    )
