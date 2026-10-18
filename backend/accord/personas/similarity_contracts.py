"""Private similarity receipts; no vectors, browser thresholds or identity probabilities."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from accord.personas.contracts import PersonaVersion
from accord.personas.face_contracts import FaceBox, RepresentationInfo
from accord.personas.photo_contracts import Digest

Scope = Literal["current", "history"]
METHOD: Literal["exact-cosine-face-max-v1"] = "exact-cosine-face-max-v1"


class QueryReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    query_id: UUID
    source_sha256: Digest
    analysis_sha256: Digest
    thumbnail_sha256: Digest
    width: int = Field(ge=1, le=1024, strict=True)
    height: int = Field(ge=1, le=1024, strict=True)
    detector: str = Field(min_length=1, max_length=160)
    decoder_version: str = Field(min_length=1, max_length=40)
    capture_recipe: Literal["rgba-png-1024-v1"] = "rgba-png-1024-v1"
    issued_at: datetime
    expires_at: datetime
    faces: tuple[FaceBox, ...] = Field(max_length=10)
    state: Literal["no_face", "selection_required"]

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.issued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("aware query times required")
        lifetime = (self.expires_at - self.issued_at).total_seconds()
        if not 0 < lifetime <= 600 or bool(self.faces) != (self.state == "selection_required"):
            raise ValueError("invalid query lifecycle")
        if any(
            f.index != i or f.x + f.width > self.width or f.y + f.height > self.height
            for i, f in enumerate(self.faces)
        ):
            raise ValueError("invalid query geometry")
        return self


class QuerySubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    query_id: UUID


class SearchCommand(QuerySubject):
    request_id: UUID
    face_index: int = Field(ge=0, le=9, strict=True)
    scope: Scope = "current"


class SimilarityCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: PersonaVersion
    portrait_id: UUID
    generation_id: UUID
    face: FaceBox
    face_cosine: float = Field(ge=-1, le=1, allow_inf_nan=False)
    whole_cosine: float = Field(ge=-1, le=1, allow_inf_nan=False)
    compatible_references: int = Field(ge=1, le=128, strict=True)


class SimilarityPage(SearchCommand):
    workspace_id: UUID
    method: Literal["exact-cosine-face-max-v1"] = METHOD
    policy_id: str = Field(min_length=1, max_length=160)
    evidence_sha256: Digest
    representation: RepresentationInfo | None
    state: Literal[
        "candidate_review",
        "no_confident_match",
        "empty_catalogue",
        "no_compatible_references",
        "quality_blocked",
    ]
    reasons: tuple[str, ...] = Field(max_length=4)
    reference_count: int = Field(ge=0, le=128, strict=True)
    compatible_count: int = Field(ge=0, le=128, strict=True)
    items: tuple[SimilarityCandidate, ...] = Field(max_length=5)
    has_more: bool = Field(strict=True)

    @model_validator(mode="after")
    def coherent(self) -> Self:
        identities = [r.version.persona_id for r in self.items]
        if len(set(identities)) != len(identities) or any(
            r.version.workspace_id != self.workspace_id for r in self.items
        ):
            raise ValueError("unscoped or duplicate candidates")
        scores = [r.face_cosine for r in self.items]
        if scores != sorted(scores, reverse=True) or self.compatible_count > self.reference_count:
            raise ValueError("invalid ranking counts")
        if bool(self.items) != (self.state == "candidate_review"):
            raise ValueError("invalid result state")
        if self.has_more and len(self.items) != 5:
            raise ValueError("invalid truncated result")
        self.validate_state()
        return self

    def validate_state(self) -> None:
        if self.state == "quality_blocked":
            if (
                self.representation
                or not self.reasons
                or self.reference_count
                or self.compatible_count
            ):
                raise ValueError("invalid quality abstention")
        elif self.representation is None or self.reasons:
            raise ValueError("representation required for ranked results")
        if self.state == "empty_catalogue" and self.reference_count:
            raise ValueError("invalid empty catalogue")
        if self.state == "no_compatible_references" and (
            not self.reference_count or self.compatible_count
        ):
            raise ValueError("invalid compatibility abstention")
        if self.state in {"candidate_review", "no_confident_match"} and not self.compatible_count:
            raise ValueError("compatible population required")


class SimilarityReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    state: Literal["processing_unavailable", "calibration_required", "calibration_expired", "ready"]
    policy_id: str | None


class ClearReceipt(QuerySubject):
    workspace_id: UUID
    closed: Literal[True] = True
