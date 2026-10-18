"""Real router/cookie responses using cryptographically verified isolated test grants."""

from unittest.mock import patch

from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from accord.auth.browser_routes import router
from auth.conftest import SigningProvider
from auth.test_browser_oidc import callback, setup


async def test_callback_keeps_tokens_server_side_and_returns_private_cookie(
    signing: SigningProvider, fake_redis: FakeRedis
) -> None:
    provider, state, _ = await setup(signing, fake_redis)
    app = FastAPI()
    app.state.session_verifier = provider
    app.include_router(router)
    with patch("accord.auth.browser_routes.get_redis", return_value=fake_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=provider.origin
        ) as client:
            client.cookies.set("accord_oidc_state", state, path="/api/auth/callback")
            result = await client.get(
                "/api/auth/callback", params={"state": state, "code": "single-use-code"}
            )
            assert result.status_code == 303 and result.headers["location"] == provider.origin + "/"
            assert result.headers["cache-control"] == "no-store"
            assert (
                "HttpOnly" in result.headers["set-cookie"]
                and "Path=/api" in result.headers["set-cookie"]
            )
            assert result.content == b""
            session = await client.get("/api/auth/session")
            assert session.status_code == 200 and session.json()["workspace_id"] == str(
                signing.workspace
            )
            assert set(session.json()) == {"workspace_id", "workspace_label", "session_key"}
            replay = await client.get(
                "/api/auth/callback", params={"state": state, "code": "single-use-code"}
            )
            assert replay.status_code == 401 and "single-use-code" not in replay.text


async def test_logout_requires_origin_and_deletes_the_server_session(
    signing: SigningProvider, fake_redis: FakeRedis
) -> None:
    provider, state, _ = await setup(signing, fake_redis)
    handle, _, _ = await provider.callback(callback(state))
    app = FastAPI()
    app.state.session_verifier = provider
    app.include_router(router)
    with patch("accord.auth.browser_routes.get_redis", return_value=fake_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=provider.origin
        ) as client:
            client.cookies.set("accord_session", handle, path="/api")
            denied = await client.post("/api/auth/logout", json={})
            assert denied.status_code == 403 and denied.headers["cache-control"] == "no-store"
            assert await provider.store.read("session", handle) is not None
            result = await client.post(
                "/api/auth/logout", json={}, headers={"Origin": provider.origin}
            )
            assert result.status_code == 200
            assert await provider.store.read("session", handle) is None
            assert (await client.get("/api/auth/session")).status_code == 401
