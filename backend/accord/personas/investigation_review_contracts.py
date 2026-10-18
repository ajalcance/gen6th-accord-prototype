"""A saved review request is a handoff, never an approval or provider finding."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class InvestigationReviewCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    version_id: UUID
    investigation_id: UUID


class InvestigationReviewReceipt(InvestigationReviewCommand):
    id: UUID
    workspace_id: UUID
    ordinal: int = Field(ge=1, strict=True)
    requester_ref: str = Field(min_length=1, max_length=160)
    requested_at: AwareDatetime
    state: Literal["requested"] = "requested"


class InvestigationReviewPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    version_id: UUID
    items: tuple[InvestigationReviewReceipt, ...] = Field(max_length=20)
    next_before_ordinal: int | None = Field(default=None, ge=1, strict=True)
