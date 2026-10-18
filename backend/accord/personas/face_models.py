"""Immutable, encrypted exact-version face processing receipts; no mutable job state."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class FaceGeneration(Base):
    __tablename__ = "persona_face_generations"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    portrait_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(160), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_id: Mapped[str] = mapped_column(String(120), nullable=False)
    wrapped_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    __table_args__ = (
        Index(
            "ix_face_subject_generation", "workspace_id", "version_id", "portrait_id", "recorded_at"
        ),
        UniqueConstraint("workspace_id", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "portrait_id"],
            [
                "persona_version_references.workspace_id",
                "persona_version_references.version_id",
                "persona_version_references.portrait_id",
            ],
        ),
        CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$' AND length(actor_ref) > 0"),
        CheckConstraint(
            "octet_length(ciphertext) BETWEEN 17 AND 131088 AND octet_length(nonce) = 12"
        ),
        CheckConstraint("octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0"),
    )
