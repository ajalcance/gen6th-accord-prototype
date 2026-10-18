"""Bounded HTTPS requests to one operator-configured Zynth origin; no redirects."""

import asyncio
import base64
import json
import ssl
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import quote_plus, urlencode, urlsplit
from urllib.request import (
    HTTPDefaultErrorHandler,
    HTTPErrorProcessor,
    HTTPSHandler,
    OpenerDirector,
    Request,
)

from pydantic import BaseModel, ConfigDict, field_validator


class ZynthSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    issuer: str
    client_id: str
    audience: str = "zynth-services"

    @field_validator("issuer")
    @classmethod
    def exact_https_origin(cls, value: str) -> str:
        parsed = urlsplit(value)
        _ = parsed.port
        if (
            not value
            or len(value) > 512
            or value != value.strip()
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Zynth issuer must be an HTTPS origin")
        return value.rstrip("/")

    @field_validator("client_id", "audience")
    @classmethod
    def required_identifier(cls, value: str) -> str:
        if not value or len(value) > 512 or value != value.strip():
            raise ValueError("Zynth identifiers must be explicit and bounded")
        return value


class ZynthTransport(Protocol):
    async def get(self, path: str, token: str | None = None) -> tuple[int, object]: ...


class ZynthHttp:
    def __init__(self, settings: ZynthSettings) -> None:
        self.origin = urlsplit(settings.issuer)

    def _request(self, request: Request) -> tuple[int, bytes, str]:
        # Only HTTPS is registered: no redirects, ambient proxies or alternate schemes.
        opener = OpenerDirector()
        opener.add_handler(HTTPSHandler(context=ssl.create_default_context()))
        opener.add_handler(HTTPDefaultErrorHandler())
        opener.add_handler(HTTPErrorProcessor())
        try:
            response = opener.open(request, timeout=2)
        except HTTPError as error:
            response = error
        with response:
            return (
                response.getcode(),
                response.read(65_537),
                response.headers.get("Content-Type", ""),
            )

    async def get(self, path: str, token: str | None = None) -> tuple[int, object]:
        return await asyncio.to_thread(self._get, path, token)

    def _get(self, path: str, token: str | None) -> tuple[int, object]:
        if path not in ("/.well-known/jwks.json", "/api/v1/oauth/userinfo"):
            raise ValueError("unsupported identity endpoint")
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        status, raw, content_type = self._request(
            Request("https://" + self.origin.netloc + path, headers=headers)
        )
        if len(raw) > 65_536:
            raise ValueError("identity response exceeds limit")
        if status != 200:
            return status, None
        if content_type.split(";", 1)[0] != "application/json":
            raise ValueError("identity response must be JSON")
        return status, json.loads(raw)

    async def exchange(self, fields: dict[str, str], client_id: str, secret: str) -> object:
        return await asyncio.to_thread(self._exchange, fields, client_id, secret)

    def _exchange(self, fields: dict[str, str], client_id: str, secret: str) -> object:
        # The one token exchange is never automatically retried: codes are single use.
        credentials = base64.b64encode(
            f"{quote_plus(client_id)}:{quote_plus(secret)}".encode()
        ).decode("ascii")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        request = Request(
            "https://" + self.origin.netloc + "/api/v1/oauth/token",
            urlencode(fields).encode(),
            headers,
        )
        status, raw, content_type = self._request(request)
        if status != 200 or len(raw) > 65_536:
            raise ValueError("identity code exchange failed")
        if content_type.split(";", 1)[0] != "application/json":
            raise ValueError("identity response must be JSON")
        return json.loads(raw)
