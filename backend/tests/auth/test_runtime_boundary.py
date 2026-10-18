"""Default app denies unconfigured identity; privileged DB roles cannot activate it."""

import ssl
from http.client import HTTPResponse
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.request import HTTPSHandler, Request
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from accord.auth.zynth_bootstrap import build_zynth_verifier
from accord.auth.zynth_http import ZynthHttp, ZynthSettings
from accord.config import Settings
from accord.main import create_app
from accord.personas.runtime_role import verify_runtime_role


async def test_default_routes_are_private_and_example_is_absent() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for path in ("login", "callback", "session"):
            response = await client.get(f"/api/auth/{path}")
            assert response.status_code == 503 and response.headers["cache-control"] == "no-store"
        assert (await client.get("/api/v1/example")).status_code == 404
        response = await client.post(
            "/api/v1/client-events",
            json={"action": "client.route_view"},
            headers={"Authorization": "Bearer user-123.sess-9.deadbeef"},
        )
        assert response.status_code == 401


def test_enabled_provider_requires_complete_configuration() -> None:
    assert build_zynth_verifier(Settings(_env_file=None, persona_api_enabled=False)) is None
    with pytest.raises(ValueError):
        build_zynth_verifier(
            Settings(
                _env_file=None,
                persona_api_enabled=True,
                zynth_tenant_id=uuid4(),
                persona_workspace_id=uuid4(),
                zynth_issuer="https://identity.example.invalid",
                zynth_client_id="accord",
            )
        )


def test_disabled_environment_template_accepts_empty_ids() -> None:
    settings = Settings.model_validate(
        {"persona_api_enabled": False, "zynth_tenant_id": "", "persona_workspace_id": ""}
    )
    assert settings.zynth_tenant_id is None and settings.persona_workspace_id is None
    assert build_zynth_verifier(settings) is None


@pytest.mark.parametrize("unsafe", [True, None])
async def test_privileged_or_unknown_runtime_role_fails_closed(unsafe: bool | None) -> None:
    session = AsyncMock()
    session.scalar.return_value = unsafe
    session.__aenter__.return_value = session
    with patch("accord.personas.runtime_role._get_sessionmaker", return_value=lambda: session):
        with pytest.raises(RuntimeError, match="confined"):
            await verify_runtime_role()
        session.scalar.return_value = False
        await verify_runtime_role()


@pytest.mark.parametrize("exchange", [False, True])
@pytest.mark.parametrize(
    "status,body,content_type",
    [
        (200, b'{"ok":true}', "application/json; charset=utf-8"),
        (302, b"", "application/json"),
        (401, b"", "application/json"),
        (200, b"x" * 65_537, "application/json"),
        (200, b"{}", "text/plain"),
    ],
    ids=["json", "redirect", "denied", "oversized", "wrong-content"],
)
def test_zynth_https_transport_bounds_and_refuses_redirects(
    exchange: bool,
    status: int,
    body: bytes,
    content_type: str,
) -> None:
    calls: list[Request] = []

    class LocalHTTPS(HTTPSHandler):
        def __init__(self, context: ssl.SSLContext) -> None:
            self.tls_context = context
            super().__init__(context=context)

        def https_open(self, request: Request) -> HTTPResponse:
            assert self.tls_context.check_hostname
            assert self.tls_context.verify_mode == ssl.CERT_REQUIRED
            assert request.timeout == 2
            calls.append(request)
            wire = (
                f"HTTP/1.1 {status} Synthetic\r\nContent-Type: {content_type}\r\n"
                "Location: https://other.example.invalid/\r\n\r\n"
            ).encode() + body
            connection = MagicMock()
            connection.makefile.return_value = BytesIO(wire)
            response = HTTPResponse(connection)
            response.begin()
            return response

    client = ZynthHttp(
        ZynthSettings(issuer="https://identity.example.invalid:443", client_id="accord")
    )
    with patch("accord.auth.zynth_http.HTTPSHandler", LocalHTTPS):
        if status == 200 and len(body) <= 65_536 and content_type.startswith("application/json"):
            result = (
                client._exchange({}, "accord", "fixture")
                if exchange
                else client._get("/.well-known/jwks.json", "fixture")
            )
            assert result == ({"ok": True} if exchange else (200, {"ok": True}))
        elif not exchange and status != 200:
            assert client._get("/.well-known/jwks.json", None) == (status, None)
        else:
            with pytest.raises(ValueError):
                if exchange:
                    client._exchange({}, "accord", "fixture")
                else:
                    client._get("/.well-known/jwks.json", None)
    assert len(calls) == 1
    assert calls[0].host == "identity.example.invalid:443"
    assert calls[0].get_method() == ("POST" if exchange else "GET")


@pytest.mark.parametrize("exchange", [False, True])
def test_zynth_tls_failure_is_not_retried(exchange: bool) -> None:
    calls: list[Request] = []

    class UntrustedHTTPS(HTTPSHandler):
        def https_open(self, request: Request) -> HTTPResponse:
            calls.append(request)
            raise ssl.SSLCertVerificationError("untrusted identity certificate")

    client = ZynthHttp(ZynthSettings(issuer="https://identity.example.invalid", client_id="accord"))
    with patch("accord.auth.zynth_http.HTTPSHandler", UntrustedHTTPS):
        with pytest.raises(ssl.SSLCertVerificationError):
            if exchange:
                client._exchange({}, "accord", "fixture")
            else:
                client._get("/.well-known/jwks.json", None)
    assert len(calls) == 1
