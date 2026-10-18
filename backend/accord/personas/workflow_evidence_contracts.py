"""References to recorded decisions and matching evidence, without signature claims."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from accord.personas.contracts import ActorRef

DecisionAction = Literal[
    "persona.review_recorded", "persona.campaign_offered", "persona.campaign_decided"
]
RecordKind = Literal["review", "campaign_offer", "campaign_decision"]


class DecisionAnchor(BaseModel):
    """Internal server-built association; never a request model."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    record_id: UUID
    workspace_id: UUID
    version_id: UUID
    action: DecisionAction
    actor_ref: ActorRef
    recorded_at: datetime
    write_request_id: UUID
    event_id: str = Field(pattern=r"^[0-9a-f]{32}$")

    @field_validator("recorded_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("decision time must include a timezone")
        return value


class WorkflowEvidence(BaseModel):
    """A matching audit entry is present, not a verified chain or platform signature."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    anchor: DecisionAnchor
    observation_request_id: UUID
    cold_event_present: bool = Field(strict=True)
    audit_state: Literal["pending", "entry_present"]
    audit_sequence: int | None = Field(ge=1, strict=True)
    audit_entry_hash: str | None = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def consistent_presence(self) -> Self:
        present = self.audit_sequence is not None and self.audit_entry_hash is not None
        absent = self.audit_sequence is None and self.audit_entry_hash is None
        if not (present if self.audit_state == "entry_present" else absent):
            raise ValueError("audit state must correspond to complete entry references")
        if not self.cold_event_present and self.audit_state == "pending":
            raise ValueError("decision evidence requires a cold event or audit entry")
        return self
