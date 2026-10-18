"""Owner-reviewed runtime configuration; browser readiness contains no resource identifiers."""

import re
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from accord.personas.google_keys import key_version
from accord.personas.similarity_policy import CalibrationPolicy


def run_origin(value: str) -> str:
    if not re.fullmatch(r"https://[a-z0-9][a-z0-9-]{0,100}\.run\.app", value):
        raise ValueError("reviewed Cloud Run origin required")
    return value


class TaskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    queue: str
    worker_origin: str
    service_email: str
    service_subject: str = Field(pattern=r"^[0-9]{10,30}$")

    @model_validator(mode="after")
    def reviewed(self) -> Self:
        if not re.fullmatch(
            r"projects/[a-z][a-z0-9-]{4,61}[a-z0-9]/locations/[a-z]+-[a-z]+[0-9]/"
            r"queues/[A-Za-z0-9-]{1,100}",
            self.queue,
        ):
            raise ValueError("invalid reviewed task queue")
        run_origin(self.worker_origin)
        project = self.queue.split("/")[1]
        if not re.fullmatch(
            r"[a-z][a-z0-9-]{4,28}[a-z0-9]@" + re.escape(project) + r"\.iam\.gserviceaccount\.com",
            self.service_email,
        ):
            raise ValueError("task identity must belong to queue project")
        return self


class GoogleRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    project: str = Field(pattern=r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")
    region: str = Field(pattern=r"^[a-z]+-[a-z]+[0-9]$")
    dimensions: int = Field(strict=True)
    wrapping_version: str
    retained_wrapping_versions: tuple[str, ...] = Field(default=(), max_length=8)
    signing_version: str | None = None
    trusted_signing_keys: dict[str, str] = Field(default_factory=dict, max_length=8)
    gemini_model: str | None = Field(default=None, pattern=r"^gemini-[a-z0-9][a-z0-9.-]{1,100}$")
    calibration: CalibrationPolicy | None = None
    tasks: TaskConfig

    @model_validator(mode="after")
    def bindings(self) -> Self:
        if self.dimensions not in {128, 256, 512, 1408}:
            raise ValueError("unsupported embedding dimension")
        versions = (self.wrapping_version, *self.retained_wrapping_versions)
        if len(set(versions)) != len(versions):
            raise ValueError("duplicate retained wrapping versions")
        for value in versions:
            key_version(value)
        for value in self.trusted_signing_keys:
            key_version(value)
        if self.signing_version:
            key_version(self.signing_version)
            if self.signing_version not in self.trusted_signing_keys or any(
                self.signing_version.rsplit("/cryptoKeyVersions/", 1)[0]
                == v.rsplit("/cryptoKeyVersions/", 1)[0]
                for v in versions
            ):
                raise ValueError("separate wrapping and trusted signing keys required")
        if self.tasks.queue.split("/")[1] != self.project:
            raise ValueError("runtime and queue project mismatch")
        if self.calibration is not None and (
            self.calibration.model != f"google/{self.region}/multimodalembedding@001"
            or self.calibration.dimensions != self.dimensions
        ):
            raise ValueError("calibration does not bind runtime encoder")
        return self


class RuntimeReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    workspace_id: UUID
    face_jobs_configured: bool
    search_configured: bool
    investigation_configured: bool
    signing_configured: bool
    verification_configured: bool
    acceptance: Literal["live_rehearsal_required"] = "live_rehearsal_required"
