"""Internal worker receipts; no content, actor identity or external delivery credentials."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class DetectionReceipt(Base):
    """Atomic evaluation checkpoint and findings, unique per source event.

    Like the command cold store, this is an internal worker table. Application reads
    must explicitly scope workspace; it has no mounted route or public access.
    No foreign key: evidence survives cold-store retention.
    """

    __tablename__ = "detection_receipts"

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rules_digest: Mapped[str] = mapped_column(String(64))
    window_within_retention: Mapped[bool] = mapped_column(Boolean)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON)

    __table_args__ = (
        Index("ix_detection_receipts_workspace_time", "workspace_id", "evaluated_at"),
    )
