"""Cloud Run metadata access only after explicit runtime assembly; no local credentials."""

import asyncio
import json
import time

import httpx

METADATA_ENDPOINT = (
    "http://metadata.google.internal/computeMetadata/v1/instance/" "service-accounts/default/token"
)


class CloudRunAccess:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.transport = transport
        self._token, self._expires = "", 0.0
        self._lock = asyncio.Lock()

    async def token(self) -> str:
        async with self._lock:
            if time.monotonic() < self._expires:
                return self._token
            async with httpx.AsyncClient(
                transport=self.transport, trust_env=False, follow_redirects=False, timeout=5
            ) as client:
                async with client.stream(
                    "GET", METADATA_ENDPOINT, headers={"Metadata-Flavor": "Google"}
                ) as response:
                    if (
                        response.status_code != 200
                        or response.headers.get("Metadata-Flavor") != "Google"
                    ):
                        raise RuntimeError("Google workload identity unavailable")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > 8192:
                            raise RuntimeError("metadata response exceeds bound")
            result = json.loads(data)
            if not isinstance(result, dict):
                raise RuntimeError("invalid workload identity response")
            token, expiry = result.get("access_token"), result.get("expires_in")
            if (
                result.get("token_type") != "Bearer"
                or not isinstance(token, str)
                or not 1 <= len(token) <= 4096
                or any(c.isspace() for c in token)
                or type(expiry) is not int
                or not 60 <= expiry <= 3600
            ):
                raise RuntimeError("invalid workload identity response")
            self._token, self._expires = token, time.monotonic() + expiry - 30
            return token
