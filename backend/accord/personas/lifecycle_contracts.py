"""Bounded declarations and human decisions; no government or legal certification."""

from datetime import UTC, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from accord.personas.contracts import ActorRef, Name, Statement

Requirement = Literal["operator", "rights", "content"]
Status = Literal["missing", "approved", "changes_requested", "withdrawn", "expired", "unavailable"]


class Value(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Operator(Value):
    name: Name
    actor_ref: ActorRef
    organization: Name | None = None
    authority: Statement
    evidence_id: UUID


class Right(Value):
    kind: Literal["likeness", "voice", "source_performance", "artwork", "other"]
    holder: Name
    scope: Statement
    withdrawal: Statement
    evidence_id: UUID
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def duration(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("rights duration must be positive")
        return self


class Provenance(Value):
    method: Literal["generated", "human_driven", "mixed"]
    provider: Name
    model_version: Name
    disclosure: Statement
    source: Literal["creator_declared"] = "creator_declared"


class Dossier(Value):
    kind: Literal["dossier"]
    operator: Operator
    rights: tuple[Right, ...] = Field(min_length=1, max_length=8)
    provenance: Provenance


class Assessment(Value):
    kind: Literal["assessment"]
    profile_id: UUID
    requirement: Requirement
    decision: Literal["approved", "changes_requested", "withdrawn"]
    statement: Statement
    valid_until: AwareDatetime


class Concern(Value):
    kind: Literal["concern"]
    category: Literal["rights", "identity", "content", "safety", "other"]
    statement: Statement


class Response(Value):
    kind: Literal["response"]
    concern_id: UUID
    decision: Literal["open", "suspended", "resolved"]
    statement: Statement


Content = Annotated[Dossier | Assessment | Concern | Response, Field(discriminator="kind")]


class Subject(Value):
    version_id: UUID


class AppendLifecycle(Subject):
    request_id: UUID
    expected_previous_id: UUID | None = None
    content: Content


class LifecycleReceipt(AppendLifecycle):
    id: UUID
    workspace_id: UUID
    persona_id: UUID
    ordinal: int = Field(ge=1, strict=True)
    actor_ref: ActorRef
    recorded_at: AwareDatetime
    evidence_digests: dict[UUID, Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]] = Field(
        default_factory=dict, max_length=9
    )


class RequirementStatus(Value):
    requirement: Requirement
    status: Status
    assessment: LifecycleReceipt | None


class ConcernStatus(Value):
    report: LifecycleReceipt
    response: LifecycleReceipt | None


class LifecycleProfile(Subject):
    workspace_id: UUID
    persona_id: UUID
    dossier: LifecycleReceipt | None
    requirements: tuple[RequirementStatus, ...] = Field(min_length=3, max_length=3)
    concerns: tuple[ConcernStatus, ...] = Field(max_length=20)
    suspended: bool
    evaluated_at: AwareDatetime


class LifecycleHistory(Subject):
    before_ordinal: int | None = Field(default=None, ge=1, strict=True)


class LifecyclePage(Value):
    workspace_id: UUID
    version_id: UUID
    items: tuple[LifecycleReceipt, ...] = Field(max_length=20)
    next_before_ordinal: int | None
    concerns: tuple[ConcernStatus, ...] = Field(default=(), max_length=20)


def effective_status(receipt: LifecycleReceipt | None, permitted: bool) -> Status:
    if receipt is None:
        return "missing"
    content = receipt.content
    if not isinstance(content, Assessment):
        raise ValueError("assessment required")
    if content.decision != "approved":
        return content.decision
    if not permitted:
        return "unavailable"
    return "expired" if content.valid_until <= datetime.now(UTC) else "approved"
