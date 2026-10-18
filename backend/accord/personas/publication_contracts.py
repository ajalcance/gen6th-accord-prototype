"""Explicit field approval. Public packages exclude all private issuance and actor identifiers."""

from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from accord.personas.passport_contracts import Integrity, SignedPassport

PublicField = Literal[
    "name",
    "biography",
    "human_contribution",
    "ai_disclosure",
    "production_name",
    "purpose",
    "conditions",
    "portrait_sha256",
]


class ApprovePublication(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    campaign_id: UUID
    fields: tuple[PublicField, ...] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def approved_fields(self) -> Self:
        if len(set(self.fields)) != len(self.fields) or not {"name", "ai_disclosure"} <= set(
            self.fields
        ):
            raise ValueError("name and AI disclosure are required; fields must be distinct")
        return self


class PublicationSubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    publication_id: UUID


class PublicProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    format: Literal["accord-public-passport-v1"] = "accord-public-passport-v1"
    publication_id: UUID
    approved_at: AwareDatetime
    valid_from: AwareDatetime
    valid_until: AwareDatetime
    version_revision: int = Field(ge=1, strict=True)
    values: dict[PublicField, str]
    claims: Literal["creator_statements_not_independently_verified"] = (
        "creator_statements_not_independently_verified"
    )

    @model_validator(mode="after")
    def projection_bounds(self) -> Self:
        if (
            not {"name", "ai_disclosure"} <= self.values.keys()
            or len(self.values) > 8
            or any(not value.strip() or len(value) > 500 for value in self.values.values())
            or self.valid_until <= self.valid_from
        ):
            raise ValueError("invalid public projection")
        return self


class PublicationReceipt(PublicationSubject):
    workspace_id: UUID
    path: str
    package: SignedPassport


class PublicVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    integrity: Integrity
    current_use: Literal["eligible", "blocked", "unavailable"]
    evaluated_at: AwareDatetime


class PublicationPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    package: SignedPassport
    verification: PublicVerification


class PublicationHistoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    campaign_id: UUID
    after_id: UUID | None = None


class PublicationHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    receipt: PublicationReceipt
    withdrawn: bool


class PublicationHistoryPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    campaign_id: UUID
    items: tuple[PublicationHistoryItem, ...] = Field(max_length=20)
    next_after_id: UUID | None = None
