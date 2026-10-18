"""Explicit owner enrollment of inspected bytes, separate from quarantine intake."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from accord.personas.campaign_contracts import AssetSnapshot
from accord.personas.contracts import Name, Statement


class EnrollAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    version_id: UUID
    evidence_id: UUID
    label: Name
    permission_statement: Statement


class EnrolledAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    version_id: UUID
    evidence_id: UUID
    asset: AssetSnapshot
