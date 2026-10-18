"""Owner-reviewed held-out evidence is injected; no shipped similarity thresholds."""

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from accord.personas.face_contracts import FaceResult, RepresentationInfo
from accord.personas.photo_contracts import Digest
from accord.personas.similarity_contracts import QueryReceipt


class CalibrationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    policy_id: str = Field(min_length=1, max_length=160)
    dataset_id: str = Field(min_length=1, max_length=160)
    run_id: str = Field(min_length=1, max_length=160)
    evidence_sha256: Digest
    model: str = Field(min_length=1, max_length=160)
    provider_revision: str = Field(min_length=1, max_length=160)
    dimensions: int = Field(ge=1, le=1408, strict=True)
    detector: str = Field(min_length=1, max_length=160)
    decoder_version: str = Field(min_length=1, max_length=40)
    capture_recipe: Literal["rgba-png-1024-v1"] = "rgba-png-1024-v1"
    crop_recipe: Literal["face-square-512-v1"] = "face-square-512-v1"
    quality_policy: Literal["provisional-face-v1"] = "provisional-face-v1"
    method: Literal["exact-cosine-face-max-v1"] = "exact-cosine-face-max-v1"
    threshold: float = Field(ge=-1, le=1, allow_inf_nan=False)
    margin: float = Field(gt=0, le=2, allow_inf_nan=False)
    reviewed_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def reviewed(self) -> Self:
        if (
            self.reviewed_at.tzinfo is None
            or self.expires_at.tzinfo is None
            or self.expires_at <= self.reviewed_at
            or self.provider_revision == "publisher-alias-unresolved"
        ):
            raise ValueError("reviewed calibration binding required")
        return self

    def matches(self, info: RepresentationInfo, detector: str, decoder: str, recipe: str) -> bool:
        return (
            info.model == self.model
            and info.provider_revision == self.provider_revision
            and info.dimensions == self.dimensions
            and info.crop_recipe == self.crop_recipe
            and info.quality_policy == self.quality_policy
            and detector == self.detector
            and decoder == self.decoder_version
            and recipe == self.capture_recipe
        )

    def query_matches(self, receipt: QueryReceipt, info: RepresentationInfo) -> bool:
        return self.matches(info, receipt.detector, receipt.decoder_version, receipt.capture_recipe)

    def reference_matches(self, result: FaceResult, decoder: str, recipe: str) -> bool:
        return result.representation is not None and self.matches(
            result.representation, result.detector, decoder, recipe
        )
