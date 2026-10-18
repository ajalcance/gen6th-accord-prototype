"""Bounded campaign scopes and immutable server receipts."""

from datetime import UTC, datetime, timedelta
from typing import Literal, Self, cast
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

from accord.personas.contracts import ActorRef, Name, Statement
from accord.personas.production_contracts import ProductionUse


class CampaignScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: Name
    recipient_ref: ActorRef
    asset_ids: tuple[UUID, ...] = Field(min_length=1, max_length=20)
    purpose: Statement
    conditions: Statement
    starts_at: datetime
    ends_at: datetime
    production: ProductionUse | None = None

    @model_serializer(mode="wrap")
    def legacy_scope(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        data = cast(dict[str, object], handler(self))
        if self.production is None:
            data.pop("production", None)
        return data

    @field_validator("asset_ids")
    @classmethod
    def distinct_assets(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        if len(set(value)) != len(value):
            raise ValueError("campaign asset IDs must be distinct")
        return tuple(sorted(value, key=str))

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("campaign times must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def bounded_duration(self) -> Self:
        if not timedelta(0) < self.ends_at - self.starts_at <= timedelta(days=366):
            raise ValueError("campaign duration must be positive and at most 366 days")
        if (
            self.production is not None
            and self.production.use_mode == "trial"
            and self.ends_at - self.starts_at > timedelta(days=30)
        ):
            raise ValueError("trial duration may not exceed 30 days")
        return self


class OfferCampaignCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    version_id: UUID
    review_id: UUID
    scope: CampaignScope


class CampaignDecisionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    campaign_id: UUID
    expected_previous_id: UUID | None = None
    decision: Literal["accepted", "changes_requested", "revoked"]
    statement: Statement


class CampaignHistoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    campaign_id: UUID
    before_ordinal: int | None = Field(default=None, ge=1, strict=True)
    limit: int = Field(default=50, ge=1, le=100, strict=True)


class AssetSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    label: Name


class CampaignReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    workspace_id: UUID
    version_id: UUID
    review_id: UUID
    owner_ref: ActorRef
    scope: CampaignScope
    assets: tuple[AssetSnapshot, ...] = Field(min_length=1, max_length=20)
    recorded_at: datetime
    event_id: str = Field(pattern=r"^[0-9a-f]{32}$")

    @field_validator("recorded_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return CampaignScope.aware_time(value)

    @model_validator(mode="after")
    def exact_asset_bindings(self) -> Self:
        if self.owner_ref == self.scope.recipient_ref:
            raise ValueError("campaign recipient must be independent of the owner")
        if tuple(asset.id for asset in self.assets) != self.scope.asset_ids:
            raise ValueError("receipt assets must exactly match the canonical scope")
        return self


class CampaignDecisionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    workspace_id: UUID
    campaign_id: UUID
    ordinal: int = Field(ge=1, strict=True)
    actor_ref: ActorRef
    decision: Literal["accepted", "changes_requested", "revoked"]
    statement: Statement
    recorded_at: datetime
    event_id: str = Field(pattern=r"^[0-9a-f]{32}$")

    @field_validator("recorded_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return CampaignScope.aware_time(value)


class CampaignDecisionPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[CampaignDecisionReceipt, ...] = Field(max_length=100)
    next_before_ordinal: int | None = Field(default=None, ge=1, strict=True)


BlockingReason = Literal[
    "stale_version",
    "review_changed",
    "reviewer_permission_removed",
    "owner_permission_removed",
    "recipient_permission_removed",
    "awaiting_acceptance",
    "changes_requested",
    "revoked",
    "not_started",
    "expired",
    "supporting_evidence_unavailable",
    "lifecycle_unavailable",
    "performer_suspended",
    "governance_missing",
    "governance_changed",
    "operator_unavailable",
    "governance_review_required",
    "governance_expired",
    "rights_window_unavailable",
    "voice_rights_missing",
]


class CampaignStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    receipt: CampaignReceipt
    latest_decision: CampaignDecisionReceipt | None
    evaluated_at: datetime
    blocking_reasons: tuple[BlockingReason, ...]
    eligible_for_use: bool = Field(strict=True)

    @field_validator("evaluated_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        return CampaignScope.aware_time(value)

    @model_validator(mode="after")
    def consistent_eligibility(self) -> Self:
        if self.eligible_for_use != (not self.blocking_reasons):
            raise ValueError("eligibility must match blocking reasons")
        if self.eligible_for_use and (
            self.latest_decision is None or self.latest_decision.decision != "accepted"
        ):
            raise ValueError("campaign use requires recorded recipient acceptance")
        if self.latest_decision is not None and (
            self.latest_decision.campaign_id != self.receipt.id
            or self.latest_decision.workspace_id != self.receipt.workspace_id
        ):
            raise ValueError("decision receipt belongs to another campaign")
        if self.latest_decision is not None:
            expected_actor = (
                self.receipt.owner_ref
                if self.latest_decision.decision == "revoked"
                else self.receipt.scope.recipient_ref
            )
            if self.latest_decision.actor_ref != expected_actor:
                raise ValueError("decision actor does not match campaign permission")
        if self.eligible_for_use and not (
            self.receipt.scope.starts_at <= self.evaluated_at < self.receipt.scope.ends_at
        ):
            raise ValueError("campaign use is outside the campaign duration")
        return self
