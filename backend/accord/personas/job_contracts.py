"""Durable reference-only face jobs; no browser-selected actor, provider or image payload."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from accord.personas.face_contracts import FaceCommand, FaceSubject

JobState = Literal["queued", "dispatched", "running", "succeeded", "failed", "cancelled"]


class JobUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    job_id: UUID
    request_id: UUID
    expected_sequence: int = Field(ge=0, le=32, strict=True)
    action: Literal["retry", "cancel"]


class JobReceipt(FaceSubject):
    job_id: UUID
    workspace_id: UUID
    command: FaceCommand
    state: JobState
    sequence: int = Field(ge=0, le=32, strict=True)
    attempts: int = Field(ge=0, le=3, strict=True)
    recorded_at: datetime
    updated_at: datetime
    lease_until: datetime | None
    generation_id: UUID | None
    recovery_available: bool

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if (
            self.command.request_id != self.job_id
            or self.command.version_id != self.version_id
            or self.command.portrait_id != self.portrait_id
            or self.recorded_at.tzinfo is None
            or self.updated_at.tzinfo is None
            or self.updated_at < self.recorded_at
            or (self.state == "succeeded") != (self.generation_id is not None)
            or (self.state == "running") != (self.lease_until is not None)
            or (self.state in {"succeeded", "cancelled"} and self.recovery_available)
            or (self.recovery_available and (self.attempts >= 3 or self.sequence >= 29))
            or (
                self.lease_until is not None
                and (self.lease_until.tzinfo is None or self.lease_until <= self.updated_at)
            )
        ):
            raise ValueError("invalid job receipt binding")
        return self


class JobPage(FaceSubject):
    workspace_id: UUID
    items: tuple[JobReceipt, ...] = Field(max_length=20)
    overflow: bool

    @model_validator(mode="after")
    def bound(self) -> Self:
        identities = set()
        for item in self.items:
            if (
                item.workspace_id != self.workspace_id
                or item.version_id != self.version_id
                or item.portrait_id != self.portrait_id
                or item.job_id in identities
            ):
                raise ValueError("invalid job page binding")
            identities.add(item.job_id)
        return self
