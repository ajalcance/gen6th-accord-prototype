"""Prepared trusted-session boundary; no identity provider or scaffold-token fallback."""

import asyncio
from datetime import UTC, datetime
from typing import Literal, Protocol, Self
from uuid import UUID

from fastapi import Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError, model_validator

from accord.personas.contracts import ActorRef
from accord.personas.workflow_contracts import WorkflowActor


class PersonaSession(BaseModel):
    """Server-verifier output only, never a request payload or workspace grant."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    actor_ref: ActorRef
    session_id: ActorRef
    kind: Literal["human"]
    issued_at: AwareDatetime
    expires_at: AwareDatetime
    workspace_id: UUID | None = None

    @model_validator(mode="after")
    def ordered_times(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("session expiry must follow issuance")
        return self


class PersonaSessionVerifier(Protocol):
    """Verify credentials, issuer/audience and current revocation/account/human status.

    Recheck every request. Return None for invalid or ambiguous credentials, and raise
    on provider failure. Do not trust browser actor/role/time fields or scaffold tokens.
    A concrete provider and its activation require separate identity/security review.
    """

    async def verify(self, request: Request) -> PersonaSession | None: ...


class SessionUnavailableError(Exception):
    """No trusted provider, invalid provider output, timeout or verification failure."""


class SessionDeniedError(Exception):
    """Missing, revoked, invalid, expired or not-yet-valid session."""


async def resolve_actor(request: Request, verifier: PersonaSessionVerifier | None) -> WorkflowActor:
    """Resolve once per request; database membership remains a separate service check."""
    if verifier is None:
        raise SessionUnavailableError
    try:
        async with asyncio.timeout(3):
            verified = await verifier.verify(request)
    except SessionDeniedError:
        raise
    except Exception as exc:
        raise SessionUnavailableError from exc
    if verified is None:
        raise SessionDeniedError
    if not isinstance(verified, PersonaSession):
        raise SessionUnavailableError
    try:
        verified = PersonaSession.model_validate(verified.model_dump())
    except ValidationError as exc:
        raise SessionUnavailableError from exc
    now = datetime.now(UTC)
    if verified.issued_at > now or verified.expires_at <= now:
        raise SessionDeniedError
    if verified.workspace_id is not None:
        requested = request.path_params.get("workspace_id")
        if requested is not None and str(verified.workspace_id) != str(requested):
            raise SessionDeniedError
    request.state.verified_sid = verified.session_id
    return WorkflowActor(actor_ref=verified.actor_ref, kind="human")
