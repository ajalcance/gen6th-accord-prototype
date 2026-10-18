"""Private evidence boundaries; these are not campaign asset contracts."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

MAX_EVIDENCE_BYTES = 10 * 1024 * 1024
MediaType = Literal["image/png", "image/jpeg", "text/plain"]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class EvidenceIntent(BaseModel):
    """Metadata only. Actor, storage location and scan outcome are never client inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    version_id: UUID
    media_type: MediaType
    byte_length: int = Field(ge=1, le=MAX_EVIDENCE_BYTES, strict=True)
    sha256: Digest


class EvidenceSnapshot(BaseModel):
    """Safe metadata; never includes plaintext, ciphertext, keys or storage addresses."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    workspace_id: UUID
    version_id: UUID
    media_type: MediaType
    byte_length: int = Field(ge=1, le=MAX_EVIDENCE_BYTES, strict=True)
    sha256: Digest
    recorded_at: AwareDatetime
    expires_at: AwareDatetime
    state: Literal["quarantined", "clean", "rejected", "expired"]


class Inspection(BaseModel):
    """Trusted scanner+decoder result bound to the exact bytes, never a browser report.

    Implementations must fully decode allowed media with bounded resources, check malware
    with current definitions, and return unavailable on timeout or incomplete inspection.
    A clean result establishes only this inspection, never originality or ownership.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    sha256: Digest
    byte_length: int = Field(ge=1, le=MAX_EVIDENCE_BYTES, strict=True)
    detected_type: MediaType
    verdict: Literal["clean", "rejected"]
    engine: str = Field(min_length=1, max_length=80)
    definitions: str = Field(min_length=1, max_length=80)
    inspected_at: AwareDatetime


def effective_state(
    expires_at: datetime, now: datetime, verdict: str | None
) -> Literal["quarantined", "clean", "rejected", "expired"]:
    if now >= expires_at:
        return "expired"
    if verdict == "clean":
        return "clean"
    if verdict == "rejected":
        return "rejected"
    return "quarantined"
