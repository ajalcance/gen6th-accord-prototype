"""Immutable inspected portraits and exact-version bindings; encrypted bytes stay private."""

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


class Portrait(Base):
    __tablename__ = "persona_portraits"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(24), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    thumbnail_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_length: Mapped[int] = mapped_column(nullable=False)
    width: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    engine: Mapped[str] = mapped_column(String(80), nullable=False)
    definitions: Mapped[str] = mapped_column(String(80), nullable=False)
    derivative_definitions: Mapped[str] = mapped_column(String(80), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "owner_ref", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "owner_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("media_type IN ('image/png', 'image/jpeg')"),
        CheckConstraint("byte_length BETWEEN 1 AND 10485760"),
        CheckConstraint("width BETWEEN 1 AND 320 AND height BETWEEN 1 AND 320"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$' AND thumbnail_sha256 ~ '^[0-9a-f]{64}$'"),
        CheckConstraint("expires_at = recorded_at + interval '24 hours'"),
        CheckConstraint(
            "length(trim(engine)) > 0 AND length(trim(definitions)) > 0 "
            "AND length(trim(derivative_definitions)) > 0"
        ),
    )


class PortraitPayload(Base):
    __tablename__ = "persona_portrait_payloads"
    portrait_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    part: Mapped[str] = mapped_column(String(16), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_id: Mapped[str] = mapped_column(String(120), nullable=False)
    wrapped_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "portrait_id"],
            ["persona_portraits.workspace_id", "persona_portraits.id"],
        ),
        CheckConstraint("part IN ('original', 'thumbnail')"),
        CheckConstraint("octet_length(ciphertext) BETWEEN 17 AND 10485776"),
        CheckConstraint("part != 'thumbnail' OR octet_length(ciphertext) <= 1048592"),
        CheckConstraint("octet_length(nonce) = 12"),
        CheckConstraint("octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0"),
    )


class VersionPortrait(Base):
    __tablename__ = "persona_version_portraits"
    version_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    portrait_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["persona_versions.workspace_id", "persona_versions.id"]
        ),
        ForeignKeyConstraint(
            ["workspace_id", "portrait_id"],
            ["persona_portraits.workspace_id", "persona_portraits.id"],
        ),
    )
