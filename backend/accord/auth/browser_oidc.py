"""Confidential OIDC relying party: PKCE, state, nonce and bounded server-side sessions."""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from urllib.parse import urlencode, urlsplit

from fastapi import Request

from accord.auth.browser_store import BrowserStore
from accord.auth.zynth_http import ZynthHttp, ZynthSettings
from accord.auth.zynth_session import ZynthSessionVerifier
from accord.auth.zynth_tokens import (
    AccessIdentity,
    InvalidZynthTokenError,
    token_parts,
    verified_claims,
    verify_signature,
)
from accord.personas.session_boundary import PersonaSession, SessionDeniedError

SESSION_COOKIE = "accord_session"
STATE_COOKIE = "accord_oidc_state"


def app_origin(value: str, development: bool) -> tuple[str, bool]:
    parsed = urlsplit(value)
    loopback = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.scheme not in ("http", "https")
        or (parsed.scheme != "https" and not (development and loopback))
    ):
        raise ValueError("application origin must be HTTPS or development loopback HTTP")
    return value.rstrip("/"), parsed.scheme == "https"


def csrf(request: Request, origin: str) -> None:
    if request.headers.get("origin") != origin:
        raise SessionDeniedError


class BrowserOidc:
    def __init__(
        self,
        settings: ZynthSettings,
        secret: str,
        origin: str,
        store: BrowserStore,
        verifier: ZynthSessionVerifier,
    ) -> None:
        self.settings, self.secret, self.origin = settings, secret, origin
        self.store, self.verifier = store, verifier
        self.http = ZynthHttp(settings)

    async def login(self) -> tuple[str, str]:
        state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        await self.store.put("flow", state, {"nonce": nonce, "verifier": verifier}, 300)
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.settings.client_id,
                "redirect_uri": f"{self.origin}/api/auth/callback",
                "scope": "openid",
                "state": state,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{self.settings.issuer}/api/v1/oauth/authorize?{query}", state

    async def callback(self, request: Request) -> tuple[str, int, PersonaSession]:
        state = request.query_params.get("state", "")
        cookie = request.cookies.get(STATE_COOKIE, "")
        if not state or len(state) > 128 or not hmac.compare_digest(state, cookie):
            raise SessionDeniedError
        flow = await self.store.read("flow", state, consume=True)
        if (
            flow is None
            or request.query_params.get("error")
            or set(request.query_params) != {"code", "state"}
            or len(request.query_params.getlist("code")) != 1
            or len(request.query_params.getlist("state")) != 1
        ):
            raise SessionDeniedError
        response = await self.exchange(request.query_params["code"], flow["verifier"])
        access, id_token = response["access_token"], response["id_token"]
        identity = await self.validate_id_token(id_token, access, flow["nonce"])
        verified = await self.verify_exchange(access, identity)
        seconds = min(3600, int((verified.expires_at - datetime.now(UTC)).total_seconds()))
        if seconds < 1:
            raise SessionDeniedError
        handle = secrets.token_urlsafe(32)
        await self.store.put("session", handle, {"access_token": access}, seconds)
        return handle, seconds, verified

    async def exchange(self, code: str, verifier: str) -> dict[str, str]:
        if not code or len(code) > 2048:
            raise SessionDeniedError
        response = await self.http.exchange(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{self.origin}/api/auth/callback",
                "code_verifier": verifier,
                "client_id": self.settings.client_id,
            },
            self.settings.client_id,
            self.secret,
        )
        if (
            not isinstance(response, dict)
            or response.get("token_type") != "Bearer"
            or not isinstance(response.get("access_token"), str)
            or not isinstance(response.get("id_token"), str)
        ):
            raise InvalidZynthTokenError
        return {"access_token": response["access_token"], "id_token": response["id_token"]}

    async def verify_exchange(self, access: str, identity: AccessIdentity) -> PersonaSession:
        scope = {"type": "http", "headers": [(b"authorization", f"Bearer {access}".encode())]}
        verified = await self.verifier.verify(Request(scope))
        access_identity = verified_claims(token_parts(access)[1], self.settings)
        if (
            verified is None
            or verified.session_id != identity.session_id
            or access_identity.subject != identity.subject
            or access_identity.tenant != identity.tenant
        ):
            raise SessionDeniedError
        return verified

    async def validate_id_token(self, token: str, access: str, nonce: str) -> AccessIdentity:
        head, body, message, signature = token_parts(token)
        verify_signature(await self.verifier.signing_key(head["kid"]), message, signature)
        now = datetime.now(UTC).timestamp()
        digest = (
            base64.urlsafe_b64encode(hashlib.sha256(access.encode()).digest()[:16])
            .decode()
            .rstrip("=")
        )
        if (
            body.get("iss") != self.settings.issuer
            or body.get("aud") != self.settings.client_id
            or body.get("nonce") != nonce
            or body.get("at_hash") != digest
            or type(body.get("iat")) is not int
            or type(body.get("exp")) is not int
            or not body["iat"] <= now < body["exp"]
            or body["exp"] <= body["iat"]
            or not isinstance(body.get("sid"), str)
            or not 1 <= len(body["sid"]) <= 64
            or body.get("tid") != str(self.verifier.tenant)
        ):
            raise InvalidZynthTokenError
        return AccessIdentity(
            subject=body["sub"],
            tenant=body["tid"],
            session_id=body["sid"],
            issued_at=datetime.fromtimestamp(body["iat"], UTC),
            expires_at=datetime.fromtimestamp(body["exp"], UTC),
        )

    async def verify(self, request: Request) -> PersonaSession | None:
        if len(request.headers.getlist("authorization")) > 1:
            raise SessionDeniedError
        if request.headers.get("authorization"):
            return await self.verifier.verify(request)
        handle = request.cookies.get(SESSION_COOKIE, "")
        if not handle or len(handle) > 128:
            return None
        if request.method not in ("GET", "HEAD"):
            csrf(request, self.origin)
            if request.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                raise SessionDeniedError
        body = await self.store.read("session", handle)
        if body is None:
            return None
        token = body.get("access_token")
        if not isinstance(token, str):
            raise InvalidZynthTokenError
        scope = dict(request.scope)
        scope["headers"] = [(b"authorization", f"Bearer {token}".encode())]
        return await self.verifier.verify(Request(scope))
