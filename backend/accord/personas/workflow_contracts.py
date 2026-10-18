"""Decision intents; caller identity is deliberately outside these payloads."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from accord.personas.contracts import ActorRef, Statement


class WorkflowActor(BaseModel):
    """Trusted internal context, never parsed from an HTTP body or scaffold token.

    Human classification must come from the verified server session.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    actor_ref: ActorRef
    kind: Literal["human", "agent", "service"]

    @property
    def audit_type(self) -> Literal["user", "agent", "system"]:
        if self.kind == "human":
            return "user"
        return "agent" if self.kind == "agent" else "system"


class ReviewHistoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version_id: UUID
    before_ordinal: int | None = Field(default=None, ge=1, strict=True)
    limit: int = Field(default=50, ge=1, le=100, strict=True)


class ReviewCommand(BaseModel):
    """Optimistic decision intent for one immutable version."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    version_id: UUID
    expected_previous_id: UUID | None = None
    decision: Literal["approved", "changes_requested"]
    statement: Statement


class ReviewSnapshot(BaseModel):
    """Immutable decision receipt; approval does not establish legal rights."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    workspace_id: UUID
    version_id: UUID
    ordinal: int = Field(ge=1, strict=True)
    reviewer_ref: ActorRef
    decision: Literal["approved", "changes_requested"]
    statement: Statement
    recorded_at: datetime
    event_id: str = Field(pattern=r"^[0-9a-f]{32}$")

    @field_validator("recorded_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recorded_at must include a timezone")
        return value.astimezone(UTC)


class ReviewPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[ReviewSnapshot, ...] = Field(max_length=100)
    next_before_ordinal: int | None = Field(default=None, ge=1, strict=True)
