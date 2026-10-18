"""Bounded portrait intents. No identity, path or scanner verdict comes from a client."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class PhotoUpload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: UUID
    media_type: Literal["image/png", "image/jpeg"]
    byte_length: int = Field(ge=1, le=10485760, strict=True)
    sha256: Digest
    # JSON preserves the existing cookie/Origin/CSRF contract; the HTTP body is bounded first.
    data: str = Field(min_length=4, max_length=13981016)


class PhotoChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action: Literal["keep", "remove", "attach"] = "keep"
    upload_id: UUID | None = None

    @model_validator(mode="after")
    def attachment(self) -> Self:
        if (self.action == "attach") != (self.upload_id is not None):
            raise ValueError("attachment requires exactly one upload identifier")
        return self


class PhotoReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    workspace_id: UUID
    request_id: UUID
    sha256: Digest
    width: int = Field(ge=1, le=320, strict=True)
    height: int = Field(ge=1, le=320, strict=True)


class PhotoUnavailableError(RuntimeError):
    """Unavailable scanner, decoder or key provider; never a clean verdict."""


class PhotoRejectedError(ValueError):
    """Malformed or unsafe input; exception details never enter a response."""
