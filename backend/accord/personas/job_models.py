"""Append-only job intent and transition ledger; no mutable lease or embedded pixels."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class FaceJob(Base):
    __tablename__ = "persona_face_jobs"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    portrait_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(160), nullable=False)
    config_id: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    command: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "portrait_id"],
            [
                "persona_version_references.workspace_id",
                "persona_version_references.version_id",
                "persona_version_references.portrait_id",
            ],
        ),
        CheckConstraint(
            "length(actor_ref) BETWEEN 1 AND 160 AND fingerprint ~ '^[0-9a-f]{64}$' "
            "AND config_id ~ '^[0-9a-f]{64}$'"
        ),
        CheckConstraint("jsonb_typeof(command) = 'object' AND octet_length(command::text) <= 4096"),
        Index("ix_face_jobs_subject", "workspace_id", "version_id", "portrait_id", "recorded_at"),
    )


class FaceJobTransition(Base):
    __tablename__ = "persona_face_job_transitions"
    workspace_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    job_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    dispatch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_id: Mapped[UUID | None] = mapped_column(Uuid)
    __table_args__ = (
        UniqueConstraint("workspace_id", "request_id"),
        ForeignKeyConstraint(
            ["workspace_id", "job_id"], ["persona_face_jobs.workspace_id", "persona_face_jobs.id"]
        ),
        ForeignKeyConstraint(["generation_id"], ["persona_face_generations.id"]),
        CheckConstraint("sequence BETWEEN 0 AND 32 AND attempts BETWEEN 0 AND 3"),
        CheckConstraint(
            "fingerprint ~ '^[0-9a-f]{64}$' AND state IN "
            "('queued','dispatched','running','succeeded','failed','cancelled')"
        ),
        CheckConstraint(
            "(state = 'running') = (lease_until IS NOT NULL) AND "
            "(state = 'succeeded') = (generation_id IS NOT NULL)"
        ),
    )
