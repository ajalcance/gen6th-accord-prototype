"""Immutable encrypted analysis captures and explicitly approved version reference sets."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class PortraitCapture(Base):
    __tablename__ = "persona_portrait_captures"
    portrait_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_width: Mapped[int] = mapped_column(nullable=False)
    source_height: Mapped[int] = mapped_column(nullable=False)
    orientation: Mapped[int] = mapped_column(nullable=False)
    width: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    recipe: Mapped[str] = mapped_column(String(40), nullable=False)
    decoder_version: Mapped[str] = mapped_column(String(40), nullable=False)
    scanner_engine: Mapped[str] = mapped_column(String(80), nullable=False)
    scanner_definitions: Mapped[str] = mapped_column(String(80), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_id: Mapped[str] = mapped_column(String(120), nullable=False)
    wrapped_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "portrait_id"),
        ForeignKeyConstraint(
            ["workspace_id", "portrait_id"],
            ["persona_portraits.workspace_id", "persona_portraits.id"],
        ),
        CheckConstraint(
            "source_width BETWEEN 1 AND 4096 AND source_height BETWEEN 1 AND 4096 "
            "AND source_width * source_height <= 8000000"
        ),
        CheckConstraint(
            "orientation BETWEEN 1 AND 8 AND width BETWEEN 1 AND 1024 AND height BETWEEN 1 AND 1024"
        ),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$' AND recipe = 'rgba-png-1024-v1'"),
        CheckConstraint(
            "length(trim(decoder_version)) > 0 AND length(trim(scanner_engine)) > 0 "
            "AND length(trim(scanner_definitions)) > 0"
        ),
        CheckConstraint(
            "octet_length(ciphertext) BETWEEN 17 AND 5242896 AND octet_length(nonce) = 12"
        ),
        CheckConstraint("octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0"),
    )


class VersionReference(Base):
    __tablename__ = "persona_version_references"
    version_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    portrait_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "version_id", "position"),
        UniqueConstraint("workspace_id", "version_id", "portrait_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["persona_versions.workspace_id", "persona_versions.id"]
        ),
        ForeignKeyConstraint(
            ["workspace_id", "portrait_id"],
            ["persona_portrait_captures.workspace_id", "persona_portrait_captures.portrait_id"],
        ),
        CheckConstraint("position BETWEEN 1 AND 8"),
    )
