"""State, PKCE, nonce, token separation, encrypted storage and Origin protections."""

import base64
import hashlib
import secrets
from typing import cast
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.exceptions import InvalidTag
from fakeredis.aioredis import FakeRedis
from fastapi import Request

from accord.auth.browser_oidc import BrowserOidc, app_origin
from accord.auth.browser_store import BrowserStore
from accord.auth.zynth_tokens import InvalidZynthTokenError
from accord.personas.session_boundary import SessionDeniedError
from auth.conftest import SigningProvider


def callback(state: str, code: str = "single-use-code") -> Request:
    return Request(
        {
            "type": "http",
            "headers": [(b"cookie", f"accord_oidc_state={state}".encode())],
            "query_string": f"state={state}&code={code}".encode(),
        }
    )


async def setup(signing: SigningProvider, redis: FakeRedis) -> tuple[BrowserOidc, str, str]:
    store = BrowserStore(redis, secrets.token_hex(32), "test-context")
    browser = BrowserOidc(
        signing.settings,
        secrets.token_urlsafe(32),
        "http://127.0.0.1:18664",
        store,
        signing.verifier,
    )
    browser.http = AsyncMock()
    url, state = await browser.login()
    flow = await store.read("flow", state)
    assert flow is not None
    access = signing.sign(signing.claims())
    digest = (
        base64.urlsafe_b64encode(hashlib.sha256(access.encode()).digest()[:16]).decode().rstrip("=")
    )
    identity = signing.sign(
        signing.claims(
            iss=signing.settings.issuer,
            aud=signing.settings.client_id,
            nonce=flow["nonce"],
            at_hash=digest,
        )
    )
    browser.http.exchange.return_value = {
        "token_type": "Bearer",
        "access_token": access,
        "id_token": identity,
    }
    return browser, state, url


async def test_login_pkce_callback_cookie_session_and_replay(
    signing: SigningProvider, fake_redis: FakeRedis
) -> None:
    browser, state, url = await setup(signing, fake_redis)
    query = parse_qs(urlsplit(url).query)
    assert query["code_challenge_method"] == ["S256"] and query["scope"] == ["openid"]
    handle, ttl, verified = await browser.callback(callback(state))
    assert 1 <= ttl <= 300 and verified.actor_ref == "canonical-accord-user"
    body = await browser.store.read("session", handle)
    assert body is not None and "access_token" in body
    encrypted = await fake_redis.get(browser.store.address("session", handle))
    assert isinstance(encrypted, str)
    assert body["access_token"] not in encrypted
    assert cast(AsyncMock, browser.http).exchange.await_count == 1
    with pytest.raises(SessionDeniedError):
        await browser.callback(callback(state))
    assert cast(AsyncMock, browser.http).exchange.await_count == 1
    headers = [
        (b"cookie", f"accord_session={handle}".encode()),
        (b"origin", browser.origin.encode()),
        (b"content-type", b"application/json"),
    ]
    request = Request({"type": "http", "method": "POST", "headers": headers})
    assert await browser.verify(request) == verified
    scope = dict(request.scope)
    scope["headers"] = [header for header in headers if header[0] != b"origin"]
    with pytest.raises(SessionDeniedError):
        await browser.verify(Request(scope))
    await browser.store.remove(handle)
    assert await browser.store.read("session", handle) is None


async def test_nonce_and_id_access_issuer_separation(
    signing: SigningProvider, fake_redis: FakeRedis
) -> None:
    browser, state, _ = await setup(signing, fake_redis)
    cast(AsyncMock, browser.http).exchange.return_value["id_token"] = signing.sign(signing.claims())
    with pytest.raises(InvalidZynthTokenError):
        await browser.callback(callback(state))
    assert await fake_redis.keys("accord:oidc:session:*") == []


async def test_state_mismatch_never_exchanges(
    signing: SigningProvider, fake_redis: FakeRedis
) -> None:
    browser, _, _ = await setup(signing, fake_redis)
    request = callback("other")
    request.scope["headers"] = [(b"cookie", b"accord_oidc_state=original")]
    with pytest.raises(SessionDeniedError):
        await browser.callback(request)
    cast(AsyncMock, browser.http).exchange.assert_not_awaited()


async def test_encrypted_state_is_bound_to_address_and_context(fake_redis: FakeRedis) -> None:
    key = secrets.token_hex(32)
    store = BrowserStore(fake_redis, key, "issuer-client")
    await store.put("flow", "original", {"nonce": "nonce"}, 300)
    ciphertext = await fake_redis.get(store.address("flow", "original"))
    assert isinstance(ciphertext, str)
    await fake_redis.set(store.address("flow", "other"), ciphertext)
    with pytest.raises(InvalidTag):
        await store.read("flow", "other")
    with pytest.raises(InvalidTag):
        await BrowserStore(fake_redis, key, "other-client").read("flow", "original")


@pytest.mark.parametrize(
    "value", ["http://remote.invalid", "https://host/path", "https://user@host", ""]
)
def test_app_origin_rejects_unsafe_locations(value: str) -> None:
    with pytest.raises(ValueError):
        app_origin(value, True)


def test_http_callback_is_development_loopback_only() -> None:
    assert app_origin("http://127.0.0.1:18664", True) == ("http://127.0.0.1:18664", False)
    with pytest.raises(ValueError):
        app_origin("http://127.0.0.1:18664", False)
