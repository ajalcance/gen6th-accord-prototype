"""Bounded private discovery; records are scoped before they become UI references."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from accord.personas.campaign_contracts import CampaignReceipt
from accord.personas.contracts import PersonaVersion
from accord.personas.evidence_contracts import EvidenceSnapshot


class VersionHistoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    persona_id: UUID
    before_revision: int | None = Field(default=None, ge=1, strict=True)
    limit: int = Field(default=20, ge=1, le=100, strict=True)


class VersionPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[PersonaVersion, ...] = Field(max_length=100)
    next_before_revision: int | None = Field(default=None, ge=1, strict=True)


class VersionObjectsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version_id: UUID
    after_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100, strict=True)


class CampaignPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[CampaignReceipt, ...] = Field(max_length=100)
    next_after_id: UUID | None = None


class EvidencePage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[EvidenceSnapshot, ...] = Field(max_length=100)
    next_after_id: UUID | None = None
