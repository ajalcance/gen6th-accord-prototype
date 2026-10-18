"""Verified Zynth request principals; unavailable identity never falls back to local tokens."""

from dataclasses import dataclass
from typing import cast

from fastapi import Depends, HTTPException, Request

from accord.personas.session_boundary import (
    PersonaSessionVerifier,
    SessionDeniedError,
    SessionUnavailableError,
    resolve_actor,
)

ACTOR_SYSTEM = "system"
ACTOR_USER = "user"


@dataclass(frozen=True)
class Principal:
    type: str
    id: str | None = None
    sid: str | None = None


ANONYMOUS = Principal(type=ACTOR_SYSTEM)


async def get_principal(request: Request) -> Principal:
    if not request.headers.get("authorization") and not request.cookies.get("accord_session"):
        return ANONYMOUS
    provider = cast(
        PersonaSessionVerifier | None, getattr(request.app.state, "session_verifier", None)
    )
    if provider is None:
        raise HTTPException(401, "authentication is unavailable")
    try:
        actor = await resolve_actor(request, provider)
        return Principal(
            type=ACTOR_USER, id=actor.actor_ref, sid=getattr(request.state, "verified_sid", None)
        )
    except SessionDeniedError as exc:
        raise HTTPException(401, "a current session is required") from exc
    except SessionUnavailableError as exc:
        raise HTTPException(503, "identity verification is unavailable") from exc


def require_user(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.type != ACTOR_USER:
        raise HTTPException(401, "authentication required")
    return principal
