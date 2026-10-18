"""Zynth human sessions: pinned signatures, current UserInfo and server-owned identity binding."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from fastapi import Request

from accord.auth.zynth_http import ZynthSettings, ZynthTransport
from accord.auth.zynth_tokens import (
    InvalidZynthTokenError,
    token_parts,
    verified_claims,
    verify_signature,
)
from accord.personas.session_boundary import PersonaSession, SessionUnavailableError

IdentityResolver = Callable[[str, UUID, UUID, UUID], Awaitable[str | None]]


class ZynthSessionVerifier:
    def __init__(
        self,
        settings: ZynthSettings,
        transport: ZynthTransport,
        tenant: UUID,
        workspace: UUID,
        resolve: IdentityResolver,
    ) -> None:
        if settings.audience != "zynth-services":
            raise ValueError("the UserInfo session profile requires its platform audience")
        self.settings, self.transport = settings, transport
        self.tenant, self.workspace, self.resolve = tenant, workspace, resolve
        self.keys: list[dict[str, Any]] = []
        self.fetched_at = 0.0
        self.lock = asyncio.Lock()

    async def signing_key(self, kid: str) -> dict[str, Any]:
        async with self.lock:
            cached = [key for key in self.keys if key.get("kid") == kid]
            if len(cached) == 1 and time.monotonic() - self.fetched_at < 300:
                return cached[0]
            status, body = await self.transport.get("/.well-known/jwks.json")
            if (
                status != 200
                or not isinstance(body, dict)
                or not isinstance(body.get("keys"), list)
                or not 1 <= len(body["keys"]) <= 10
                or not all(isinstance(key, dict) for key in body["keys"])
            ):
                raise SessionUnavailableError
            self.keys = body["keys"]
            self.fetched_at = time.monotonic()
            matches = [key for key in self.keys if key.get("kid") == kid]
            if len(matches) != 1:
                raise InvalidZynthTokenError
            return matches[0]

    async def verify(self, request: Request) -> PersonaSession | None:
        try:
            token = self.bearer(request)
            if token is None:
                return None
            header, body, message, signature = token_parts(token)
            verify_signature(await self.signing_key(header["kid"]), message, signature)
            identity = verified_claims(body, self.settings)
            if identity.tenant != self.tenant:
                return None
            status, profile = await self.transport.get("/api/v1/oauth/userinfo", token)
            if status in (401, 403):
                return None
            if status != 200:
                raise SessionUnavailableError
            if (
                not isinstance(profile, dict)
                or profile.get("sub") != str(identity.subject)
                or profile.get("tid") != str(identity.tenant)
            ):
                raise SessionUnavailableError
            actor = await self.resolve(
                self.settings.issuer, identity.tenant, identity.subject, self.workspace
            )
            if actor is None:
                return None
            return PersonaSession(
                actor_ref=actor,
                session_id=identity.session_id,
                kind="human",
                issued_at=identity.issued_at,
                expires_at=identity.expires_at,
                workspace_id=self.workspace,
            )
        except InvalidZynthTokenError:
            return None

    @staticmethod
    def bearer(request: Request) -> str | None:
        headers = request.headers.getlist("authorization")
        if len(headers) != 1:
            return None
        scheme, _, token = headers[0].partition(" ")
        if scheme.lower() != "bearer" or not token or any(c.isspace() for c in token):
            return None
        return token
