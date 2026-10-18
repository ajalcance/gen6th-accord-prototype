"""Cryptographic and current-session rejection; no live provider assertions."""

from uuid import uuid4

import pytest
from fastapi import Request

from accord.auth.zynth_tokens import InvalidZynthTokenError, token_parts
from accord.personas.session_boundary import (
    SessionDeniedError,
    SessionUnavailableError,
    resolve_actor,
)
from auth.conftest import SigningProvider


def request(token: str) -> Request:
    return Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})


async def test_signature_userinfo_and_binding_are_required_each_time(
    signing: SigningProvider,
) -> None:
    token = signing.sign(signing.claims())
    result = await signing.verifier.verify(request(token))
    assert result is not None and result.actor_ref == "canonical-accord-user"
    assert result.workspace_id == signing.workspace
    signing.resolve.assert_awaited_once_with(
        signing.settings.issuer, signing.tenant, signing.subject, signing.workspace
    )
    signing.status = 401
    assert await signing.verifier.verify(request(token)) is None
    assert signing.transport.get.await_count == 3  # JWKS cached; UserInfo is not cached


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://identity.example.invalid"},
        {"aud": "another-client"},
        {"client_id": "other-client"},
        {"type": "id"},
        {"actor": "oauth_client"},
        {"cnf": {}},
        {"exp": 1},
        {"iat": 9999999999},
        {"exp": True},
        {"sid": ""},
        {"sid": "x" * 65},
        {"sub": "invalid"},
        {"nbf": 9999999999},
    ],
)
async def test_wrong_token_profiles_never_reach_userinfo(
    signing: SigningProvider, changes: dict[str, object]
) -> None:
    assert await signing.verifier.verify(request(signing.sign(signing.claims(**changes)))) is None
    assert signing.resolve.await_count == 0
    assert all(call.args[0].endswith("jwks.json") for call in signing.transport.get.await_args_list)


async def test_wrong_tenant_and_unprovisioned_user_are_denied(signing: SigningProvider) -> None:
    assert (
        await signing.verifier.verify(request(signing.sign(signing.claims(tid=str(uuid4())))))
        is None
    )
    signing.resolve.return_value = None
    assert await signing.verifier.verify(request(signing.sign(signing.claims()))) is None


@pytest.mark.parametrize("status", [429, 500, 503])
async def test_userinfo_failure_is_unavailable(signing: SigningProvider, status: int) -> None:
    signing.status = status
    with pytest.raises(SessionUnavailableError):
        await resolve_actor(request(signing.sign(signing.claims())), signing.verifier)


async def test_bad_signature_and_wrong_workspace_are_denied(signing: SigningProvider) -> None:
    token = signing.sign(signing.claims())
    parts = token.split(".")
    parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
    assert await signing.verifier.verify(request(".".join(parts))) is None
    incoming = request(token)
    incoming.scope["path_params"] = {"workspace_id": uuid4()}
    with pytest.raises(SessionDeniedError):
        await resolve_actor(incoming, signing.verifier)


@pytest.mark.parametrize(
    "header", [{"alg": "HS256"}, {"jku": "https://other.invalid"}, {"crit": []}]
)
async def test_token_controlled_key_discovery_is_refused(
    signing: SigningProvider, header: dict[str, object]
) -> None:
    assert await signing.verifier.verify(request(signing.sign(signing.claims(), **header))) is None
    signing.transport.get.assert_not_awaited()


@pytest.mark.parametrize("token", ["bad", "e30.e30.AA", "x" * 16385, "=.AA.AA"])
def test_malformed_token_is_rejected(token: str) -> None:
    with pytest.raises(InvalidZynthTokenError):
        token_parts(token)
