"""Immutable evidence metadata/inspection, with independently expiring encrypted payloads."""

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


class PrivateEvidence(Base):
    __tablename__ = "persona_private_evidence"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    owner_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(String(24), nullable=False)
    byte_length: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "version_id", "id", name="uq_private_evidence_version"),
        UniqueConstraint("workspace_id", "owner_ref", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["persona_versions.workspace_id", "persona_versions.id"]
        ),
        ForeignKeyConstraint(
            ["workspace_id", "owner_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        CheckConstraint("byte_length BETWEEN 1 AND 10485760"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'"),
        CheckConstraint("media_type IN ('image/png', 'image/jpeg', 'text/plain')"),
        CheckConstraint("expires_at = recorded_at + interval '7 days'"),
    )


class EvidencePayload(Base):
    """Encrypted bytes have a shorter lifecycle than retained provenance metadata."""

    __tablename__ = "private_evidence_payloads"
    evidence_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_id: Mapped[str] = mapped_column(String(120), nullable=False)
    wrapped_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "evidence_id"],
            ["persona_private_evidence.workspace_id", "persona_private_evidence.id"],
        ),
        CheckConstraint("octet_length(ciphertext) BETWEEN 17 AND 10485776"),
        CheckConstraint("octet_length(nonce) = 12"),
        CheckConstraint("octet_length(wrapped_key) BETWEEN 1 AND 4096 AND length(key_id) > 0"),
    )


class EvidenceInspection(Base):
    __tablename__ = "persona_evidence_inspections"
    evidence_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    engine: Mapped[str] = mapped_column(String(80), nullable=False)
    definitions: Mapped[str] = mapped_column(String(80), nullable=False)
    inspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "evidence_id"],
            ["persona_private_evidence.workspace_id", "persona_private_evidence.id"],
        ),
        CheckConstraint("verdict IN ('clean', 'rejected')"),
        CheckConstraint("length(trim(engine)) > 0 AND length(trim(definitions)) > 0"),
    )
