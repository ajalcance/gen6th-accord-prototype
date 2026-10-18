"""Version-bound face processing; detector confidence is never identity confidence."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FaceBox(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    index: int = Field(ge=0, le=9)
    x: int = Field(ge=0, le=1023)
    y: int = Field(ge=0, le=1023)
    width: int = Field(ge=1, le=1024)
    height: int = Field(ge=1, le=1024)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    yaw: float = Field(ge=-180, le=180, allow_inf_nan=False)
    pitch: float = Field(ge=-180, le=180, allow_inf_nan=False)
    blur: Literal["UNKNOWN", "VERY_UNLIKELY", "UNLIKELY", "POSSIBLE", "LIKELY", "VERY_LIKELY"]


class FaceSubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version_id: UUID
    portrait_id: UUID


class FaceCommand(FaceSubject):
    request_id: UUID
    generation_id: UUID | None = None
    face_index: int | None = Field(default=None, ge=0, le=9, strict=True)

    @model_validator(mode="after")
    def selection(self) -> Self:
        if (self.generation_id is None) != (self.face_index is None):
            raise ValueError("selection requires the stored generation and face index")
        return self


class RepresentationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model: str = Field(min_length=1, max_length=160)
    provider_revision: str = Field(min_length=1, max_length=160)
    dimensions: int = Field(ge=1, le=1408, strict=True)
    crop_recipe: Literal["face-square-512-v1"] = "face-square-512-v1"
    crop_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    quality_policy: Literal["provisional-face-v1"] = "provisional-face-v1"
    calibration: Literal["benchmark_pending"] = "benchmark_pending"


class FaceResult(FaceSubject):
    workspace_id: UUID
    request_id: UUID
    generation_id: UUID
    parent_id: UUID | None
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    width: int = Field(ge=1, le=1024, strict=True)
    height: int = Field(ge=1, le=1024, strict=True)
    detector: str = Field(min_length=1, max_length=160)
    recorded_at: datetime
    faces: tuple[FaceBox, ...] = Field(max_length=10)
    selected: int | None = Field(ge=0, le=9, strict=True)
    state: Literal["no_face", "selection_required", "quality_blocked", "represented"]
    reasons: tuple[Literal["small_face", "low_detection_confidence", "extreme_pose", "blur"], ...]
    representation: RepresentationInfo | None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.recorded_at.tzinfo is None:
            raise ValueError("aware timestamp required")
        if any(
            f.index != i or f.x + f.width > self.width or f.y + f.height > self.height
            for i, f in enumerate(self.faces)
        ):
            raise ValueError("face boxes do not bind to the analysis image")
        detection = self.state in {"no_face", "selection_required"}
        if detection:
            if self.parent_id or self.selected is not None or self.reasons or self.representation:
                raise ValueError("detection cannot imply selection")
            if bool(self.faces) != (self.state == "selection_required"):
                raise ValueError("invalid detection state")
        elif (
            self.parent_id is None
            or self.selected is None
            or self.selected >= len(self.faces)
            or bool(self.representation) != (self.state == "represented")
            or bool(self.reasons) != (self.state == "quality_blocked")
        ):
            raise ValueError("invalid selected representation state")
        return self


class FaceProfile(FaceSubject):
    workspace_id: UUID
    latest: FaceResult | None
    provider_ready: bool
