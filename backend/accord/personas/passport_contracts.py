"""Bounded export projections; signatures do not establish identity or legal rights."""

from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, model_validator

from accord.personas.campaign_contracts import AssetSnapshot, CampaignReceipt, CampaignStatus
from accord.personas.capture_contracts import CaptureMetadata
from accord.personas.contracts import PersonaVersion


class PassportSubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    campaign_id: UUID


class AssetQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version_id: UUID


class AssetPage(AssetQuery):
    workspace_id: UUID
    assets: tuple[AssetSnapshot, ...] = Field(max_length=20)


class PassportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    format: Literal["accord-persona-passport-v1"] = "accord-persona-passport-v1"
    issued_at: AwareDatetime
    version: PersonaVersion
    campaign: CampaignReceipt
    acceptance_id: UUID
    references: tuple[CaptureMetadata, ...] = Field(min_length=1, max_length=8)
    claims: Literal["creator_statements_and_references_not_independently_verified"] = (
        "creator_statements_and_references_not_independently_verified"
    )

    @model_validator(mode="after")
    def exact_bindings(self) -> Self:
        if (
            self.version.workspace_id != self.campaign.workspace_id
            or self.version.version_id != self.campaign.version_id
            or self.campaign.scope.production is None
            or len({row.portrait_id for row in self.references}) != len(self.references)
        ):
            raise ValueError("passport requires an exact production and unique references")
        return self


class SignedPassport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    algorithm: Literal["Ed25519"] = "Ed25519"
    key_id: str = Field(pattern=r"^[A-Za-z0-9_./-]{1,240}$")
    payload: dict[str, JsonValue]
    signature: str = Field(pattern=r"^[A-Za-z0-9+/]{86}==$", min_length=88, max_length=88)


class VerifyPassport(PassportSubject):
    package: SignedPassport


class PassportReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    export_available: bool = Field(strict=True)
    verification_available: bool = Field(strict=True)


Integrity = Literal[
    "valid", "invalid_signature", "untrusted_key", "invalid_package", "binding_mismatch"
]


class PassportVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    campaign_id: UUID
    integrity: Integrity
    current_status: CampaignStatus | None = None

    @model_validator(mode="after")
    def separate_permission(self) -> Self:
        if (self.integrity == "valid") != (self.current_status is not None):
            raise ValueError("only valid bound packages can disclose current permission")
        if self.current_status and (
            self.current_status.receipt.workspace_id != self.workspace_id
            or self.current_status.receipt.id != self.campaign_id
        ):
            raise ValueError("current permission belongs to a different campaign")
        return self
