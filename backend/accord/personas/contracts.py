"""Bounded persona inputs and immutable version snapshots for the H2 core.

Identity, workspace membership and timestamps belong to trusted server code, never
to the input payload. These contracts do not establish rights or issue approvals.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
ActorRef = Annotated[str, StringConstraints(min_length=1, max_length=64)]
Statement = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class PersonaDraft(BaseModel):
    """Creator-supplied content only; attribution and authorization are excluded."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: Name
    biography: Statement
    human_contribution: Statement
    ai_disclosure: Statement


class PersonaVersion(BaseModel):
    """Server-built snapshot, not a request schema or a mutable draft."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    persona_id: UUID
    workspace_id: UUID
    version_id: UUID
    revision: int = Field(ge=1, strict=True)
    creator_ref: ActorRef
    recorded_at: datetime
    content: PersonaDraft

    @field_validator("recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Receipt time must be timezone-aware; it is not a claimed creation date."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recorded_at must include a timezone")
        return value
