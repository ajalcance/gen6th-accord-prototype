"""Synthetic verifier contract tests; no IdP or scaffold credentials are activated."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import Request
from pydantic import ValidationError

from accord.personas.session_boundary import (
    PersonaSession,
    SessionDeniedError,
    SessionUnavailableError,
    resolve_actor,
)


def verified(**changes: object) -> PersonaSession:
    now = datetime.now(UTC)
    return PersonaSession.model_validate(
        {
            "actor_ref": "viewer",
            "session_id": "synthetic-session",
            "kind": "human",
            "issued_at": now - timedelta(minutes=1),
            "expires_at": now + timedelta(minutes=5),
            **changes,
        }
    )


def request() -> Request:
    return Request({"type": "http", "headers": []})


async def test_missing_provider_is_unavailable() -> None:
    with pytest.raises(SessionUnavailableError):
        await resolve_actor(request(), None)


async def test_verified_human_is_resolved_again_on_every_request() -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified()
    actor = await resolve_actor(request(), provider)
    assert actor.actor_ref == "viewer" and actor.kind == "human"
    provider.verify.return_value = None
    with pytest.raises(SessionDeniedError):
        await resolve_actor(request(), provider)
    assert provider.verify.await_count == 2


@pytest.mark.parametrize("seconds", [-1, 0])
async def test_expired_session_is_denied(seconds: int) -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified(
        expires_at=datetime.now(UTC) + timedelta(seconds=seconds)
    )
    with pytest.raises(SessionDeniedError):
        await resolve_actor(request(), provider)


async def test_future_session_is_denied() -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified(issued_at=datetime.now(UTC) + timedelta(minutes=1))
    with pytest.raises(SessionDeniedError):
        await resolve_actor(request(), provider)


@pytest.mark.parametrize("error", [RuntimeError("synthetic provider failure"), TimeoutError()])
async def test_provider_failure_is_unavailable(error: Exception) -> None:
    provider = AsyncMock()
    provider.verify.side_effect = error
    with pytest.raises(SessionUnavailableError):
        await resolve_actor(request(), provider)


async def test_untyped_provider_output_cannot_become_an_actor() -> None:
    provider = AsyncMock()
    provider.verify.return_value = verified().model_dump()
    with pytest.raises(SessionUnavailableError):
        await resolve_actor(request(), provider)


async def test_provider_cannot_bypass_human_validation_with_model_construct() -> None:
    provider = AsyncMock()
    provider.verify.return_value = PersonaSession.model_construct(
        **{**verified().model_dump(), "kind": "agent"}
    )
    with pytest.raises(SessionUnavailableError):
        await resolve_actor(request(), provider)


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "agent"},
        {"role": "creator"},
        {"workspace_id": "browser claim"},
        {"actor_ref": ""},
        {"issued_at": datetime.now().replace(tzinfo=None)},
        {"expires_at": datetime.now(UTC) - timedelta(days=1)},
    ],
)
def test_session_contract_rejects_false_authority_and_invalid_times(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        verified(**changes)
