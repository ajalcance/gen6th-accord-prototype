"""Google signed service identity, never trusted Cloud Tasks headers or browser identity."""

import asyncio
import json
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from accord.auth.zynth_tokens import (
    InvalidZynthTokenError,
    token_parts,
    verify_signature,
)
from accord.personas.runtime_contracts import TaskConfig

JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"


class GoogleTaskIdentity:
    def __init__(
        self, config: TaskConfig, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.config, self.transport = config, transport
        self._keys: dict[str, dict[str, Any]] = {}
        self._expires = 0.0
        self._lock = asyncio.Lock()

    async def keys(self) -> dict[str, dict[str, Any]]:
        async with self._lock:
            if time.monotonic() < self._expires:
                return self._keys
            async with httpx.AsyncClient(
                transport=self.transport, trust_env=False, follow_redirects=False, timeout=5
            ) as client:
                async with client.stream("GET", JWKS_URL) as response:
                    if response.status_code != 200:
                        raise RuntimeError("worker trust unavailable")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > 32768:
                            raise RuntimeError("worker trust exceeds bound")
            document = json.loads(data)
            if not isinstance(document, dict):
                raise RuntimeError("invalid worker trust")
            rows = document.get("keys")
            if not isinstance(rows, list) or not 1 <= len(rows) <= 10:
                raise RuntimeError("invalid worker trust")
            chosen: dict[str, dict[str, Any]] = {}
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("kid"), str):
                    raise RuntimeError("invalid worker key")
                if row["kid"] in chosen:
                    raise RuntimeError("ambiguous worker key")
                chosen[row["kid"]] = row
            self._keys, self._expires = chosen, time.monotonic() + 300
            return chosen

    async def verify(self, token: str) -> str:
        try:
            header, claims, message, signature = token_parts(token)
            key = (await self.keys()).get(header["kid"])
            if key is None:
                raise InvalidZynthTokenError
            verify_signature(key, message, signature)
            validate_claims(claims, self.config)
            return self.config.service_email
        except (InvalidZynthTokenError, ValueError, TypeError, KeyError) as exc:
            raise PermissionError("worker identity rejected") from exc


def validate_claims(claims: dict[str, Any], config: TaskConfig) -> None:
    now = datetime.now(UTC).timestamp()
    if (
        claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}
        or claims.get("aud") != config.worker_origin
        or claims.get("email") != config.service_email
        or claims.get("sub") != config.service_subject
        or claims.get("email_verified") is not True
        or type(claims.get("iat")) is not int
        or type(claims.get("exp")) is not int
        or not claims["iat"] <= now < claims["exp"]
        or not 0 < claims["exp"] - claims["iat"] <= 3600
        or ("nbf" in claims and (type(claims["nbf"]) is not int or claims["nbf"] > now))
    ):
        raise PermissionError("worker identity rejected")
