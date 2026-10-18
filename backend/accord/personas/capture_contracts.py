"""Prepared image provenance is not a face quality or embedding readiness verdict."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from accord.personas.photo_contracts import Digest


class CaptureQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    upload_id: UUID | None = None
    version_id: UUID | None = None

    @model_validator(mode="after")
    def one_subject(self) -> Self:
        if (self.upload_id is None) == (self.version_id is None):
            raise ValueError("exactly one capture subject is required")
        return self


class CaptureMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    portrait_id: UUID
    source_sha256: Digest
    source_width: int = Field(ge=1, le=4096, strict=True)
    source_height: int = Field(ge=1, le=4096, strict=True)
    orientation: int = Field(ge=1, le=8, strict=True)
    width: int = Field(ge=1, le=1024, strict=True)
    height: int = Field(ge=1, le=1024, strict=True)
    sha256: Digest
    recipe: Literal["rgba-png-1024-v1"]
    decoder_version: str = Field(min_length=1, max_length=40)
    recorded_at: datetime

    @model_validator(mode="after")
    def bounded_provenance(self) -> Self:
        source = (
            (self.source_height, self.source_width)
            if self.orientation >= 5
            else (self.source_width, self.source_height)
        )
        if (
            self.source_width * self.source_height > 8_000_000
            or (self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None)
            or self.width > source[0]
            or self.height > source[1]
        ):
            raise ValueError("capture provenance requires bounded pixels and an aware timestamp")
        return self


class CaptureProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    upload_id: UUID | None
    version_id: UUID | None
    portrait_id: UUID | None
    capture: CaptureMetadata | None
    references: tuple[CaptureMetadata, ...] = Field(max_length=8)
    recognition: Literal["not_processed"] = "not_processed"

    @model_validator(mode="after")
    def consistent_profile(self) -> Self:
        CaptureQuery(upload_id=self.upload_id, version_id=self.version_id)
        ids = [item.portrait_id for item in self.references]
        if len(set(ids)) != len(ids) or (
            self.capture and self.capture.portrait_id != self.portrait_id
        ):
            raise ValueError("inconsistent capture references")
        if self.upload_id and (self.portrait_id != self.upload_id or self.references):
            raise ValueError("upload lookup cannot invent approved references")
        return self


class ReferenceChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action: Literal["keep", "replace"] = "keep"
    upload_ids: tuple[UUID, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def explicit_set(self) -> Self:
        if len(set(self.upload_ids)) != len(self.upload_ids) or (
            self.action == "keep" and self.upload_ids
        ):
            raise ValueError("references must be unique and explicitly replaced")
        return self
