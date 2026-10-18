"""Exact-version investigation packets; bounded observations never grant rights."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from accord.personas.face_contracts import FaceBox
from accord.personas.similarity_contracts import QueryReceipt, SearchCommand

Label = Literal[
    "facial_features_similar",
    "facial_features_different",
    "pose_differs",
    "appearance_differs",
    "comparison_uncertain",
]
Citation = Literal["query_image", "approved_reference"]
Gap = Literal["identity_not_established", "rights_not_verified", "source_context_unverified"]
GAPS: tuple[Gap, ...] = (
    "identity_not_established",
    "rights_not_verified",
    "source_context_unverified",
)
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class InvestigationCommand(SearchCommand):
    version_id: UUID
    portrait_id: UUID
    generation_id: UUID
    source_note: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    retain_findings: Literal[True]


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    label: Label
    citations: tuple[Citation, Citation]

    @model_validator(mode="after")
    def both_images(self) -> Self:
        if self.citations != ("query_image", "approved_reference"):
            raise ValueError("comparison requires both authorized images")
        return self


class ProviderFindings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: Literal["observations", "insufficient_evidence"]
    observations: tuple[Observation, ...] = Field(max_length=5)

    @model_validator(mode="after")
    def coherence(self) -> Self:
        labels = [item.label for item in self.observations]
        if len(set(labels)) != len(labels) or bool(labels) != (self.state == "observations"):
            raise ValueError("invalid observation state")
        if {"facial_features_similar", "facial_features_different"}.issubset(labels):
            raise ValueError("contradictory facial comparison")
        return self


class SearchEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    method: Literal["exact-cosine-face-max-v1"]
    policy_id: str = Field(min_length=1, max_length=160)
    evidence_sha256: Digest
    scope: Literal["current", "history"]
    face_index: int = Field(ge=0, le=9, strict=True)
    face_cosine: float = Field(ge=-1, le=1, allow_inf_nan=False)
    whole_cosine: float = Field(ge=-1, le=1, allow_inf_nan=False)


class InvestigationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    workspace_id: UUID
    version_id: UUID
    portrait_id: UUID
    generation_id: UUID
    request_id: UUID
    ordinal: int = Field(ge=1, strict=True)
    actor_ref: str = Field(min_length=1, max_length=160)
    recorded_at: AwareDatetime
    source_note: str = Field(min_length=1, max_length=500)
    query: QueryReceipt
    reference_sha256: Digest
    reference_face: FaceBox
    search: SearchEvidence
    model: str = Field(min_length=1, max_length=160)
    provider_revision: str = Field(min_length=1, max_length=160)
    recipe: Literal["grounded-comparison-v1"] = "grounded-comparison-v1"
    findings: ProviderFindings
    gaps: tuple[
        Literal["identity_not_established", "rights_not_verified", "source_context_unverified"], ...
    ] = GAPS

    @model_validator(mode="after")
    def binding(self) -> Self:
        if (
            self.query.workspace_id != self.workspace_id
            or self.gaps != GAPS
            or self.search.face_index >= len(self.query.faces)
            or self.search.request_id != self.request_id
        ):
            raise ValueError("invalid investigation evidence binding")
        return self


class InvestigationHistory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version_id: UUID
    before_ordinal: int | None = Field(default=None, ge=1, strict=True)


class InvestigationPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    version_id: UUID
    items: tuple[InvestigationResult, ...] = Field(max_length=20)
    next_before_ordinal: int | None = Field(default=None, ge=1, strict=True)


class InvestigationReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    state: Literal["processing_unavailable", "ready"]
