"""One append-only, tenant-scoped lifecycle ledger; serialised by the performer lock."""

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


class LifecycleRecord(Base):
    __tablename__ = "persona_lifecycle_records"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    persona_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    expected_previous_id: Mapped[UUID | None] = mapped_column(Uuid)
    target_id: Mapped[UUID | None] = mapped_column(Uuid)
    ordinal: Mapped[int] = mapped_column(nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    requirement: Mapped[str | None] = mapped_column(String(16))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    evidence_digests: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    __table_args__ = (
        UniqueConstraint("workspace_id", "actor_ref", "request_id"),
        UniqueConstraint("workspace_id", "persona_id", "ordinal"),
        UniqueConstraint("workspace_id", "persona_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "persona_id"], ["personas.workspace_id", "personas.id"]
        ),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["persona_versions.workspace_id", "persona_versions.id"]
        ),
        ForeignKeyConstraint(
            ["workspace_id", "persona_id", "version_id"],
            ["persona_versions.workspace_id", "persona_versions.persona_id", "persona_versions.id"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "actor_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "persona_id", "target_id"],
            [
                "persona_lifecycle_records.workspace_id",
                "persona_lifecycle_records.persona_id",
                "persona_lifecycle_records.id",
            ],
        ),
        ForeignKeyConstraint(
            ["workspace_id", "persona_id", "expected_previous_id"],
            [
                "persona_lifecycle_records.workspace_id",
                "persona_lifecycle_records.persona_id",
                "persona_lifecycle_records.id",
            ],
        ),
        CheckConstraint("ordinal >= 1 AND fingerprint ~ '^[0-9a-f]{64}$'"),
        CheckConstraint(
            "kind IN ('dossier', 'assessment', 'concern', 'response') AND content->>'kind' = kind"
        ),
        CheckConstraint("(kind IN ('assessment', 'response')) = (target_id IS NOT NULL)"),
        CheckConstraint(
            "(kind = 'assessment' AND requirement IS NOT NULL "
            "AND requirement IN ('operator', 'rights', 'content')) "
            "OR (kind <> 'assessment' AND requirement IS NULL)"
        ),
        CheckConstraint(
            "jsonb_typeof(content) = 'object' AND octet_length(content::text) <= 16000"
        ),
        CheckConstraint(
            "jsonb_typeof(evidence_digests) = 'object' "
            "AND octet_length(evidence_digests::text) <= 1500"
        ),
    )


def register_lifecycle_policies() -> None:
    table = cast(Table, LifecycleRecord.__table__)
    for statement in (*policies(table.name), immutable_trigger(table.name)):
        event.listen(table, "after_create", execute_ddl(statement))
