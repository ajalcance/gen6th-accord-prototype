"""Real RSA OIDC verification against synthetic bounded JWKS; no live service identity."""

import base64
import json
from datetime import UTC, datetime

import httpx
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from accord.personas.task_identity import GoogleTaskIdentity
from personas.runtime_fixtures import task_config


def encoded(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def material(changes: dict[str, object]) -> tuple[str, dict[str, str]]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    config = task_config()
    now = int(datetime.now(UTC).timestamp())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": config.worker_origin,
        "email": config.service_email,
        "sub": config.service_subject,
        "email_verified": True,
        "iat": now - 1,
        "exp": now + 300,
        **changes,
    }
    parts = [
        encoded(json.dumps({"alg": "RS256", "kid": "synthetic-key"}).encode()),
        encoded(json.dumps(claims).encode()),
    ]
    message = ".".join(parts).encode()
    signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    numbers = key.public_key().public_numbers()
    jwk = {
        "kid": "synthetic-key",
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": encoded(numbers.n.to_bytes(256, "big")),
        "e": encoded(numbers.e.to_bytes(3, "big")),
    }
    return message.decode() + "." + encoded(signature), jwk


@pytest.mark.asyncio
async def test_real_signature_and_exact_service_identity_are_required_before_worker_access() -> (
    None
):
    token, key = material({})
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"keys": [key]})

    identity = GoogleTaskIdentity(task_config(), httpx.MockTransport(respond))
    assert await identity.verify(token) == task_config().service_email
    assert await identity.verify(token) == task_config().service_email
    assert len(calls) == 1 and str(calls[0].url) == "https://www.googleapis.com/oauth2/v3/certs"
    head, body, signature = token.split(".")
    changed = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    changed["email"] = "different"
    with pytest.raises(PermissionError):
        await identity.verify(".".join((head, encoded(json.dumps(changed).encode()), signature)))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"aud": "https://other.run.app"},
        {"email": "different"},
        {"sub": "different"},
        {"iss": "different"},
        {"email_verified": False},
        {"iat": True},
        {"exp": 0},
        {"nbf": 9999999999},
    ],
)
async def test_signed_wrong_workload_claims_are_denied(changes: dict[str, object]) -> None:
    token, key = material(changes)
    identity = GoogleTaskIdentity(
        task_config(), httpx.MockTransport(lambda _: httpx.Response(200, json={"keys": [key]}))
    )
    with pytest.raises(PermissionError):
        await identity.verify(token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302),
        httpx.Response(200, json={"keys": []}),
        httpx.Response(200, content=b"x" * 32769),
    ],
)
async def test_unavailable_worker_trust_never_accepts_claimed_task_headers(
    response: httpx.Response,
) -> None:
    token, _key = material({})
    identity = GoogleTaskIdentity(task_config(), httpx.MockTransport(lambda _: response))
    with pytest.raises(RuntimeError):
        await identity.verify(token)
