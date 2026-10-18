"""Owner-configured persistent Vault Transit key wrapping; no key creation or fallback."""

import base64
import re
from typing import Any, cast
from urllib.parse import urlsplit

import httpx
from pydantic import SecretStr

from accord.personas.photo_contracts import PhotoUnavailableError


class VaultKeyWrapper:
    def __init__(
        self, address: str, token: SecretStr, key_name: str, *, development: bool = False
    ) -> None:
        url = urlsplit(address)
        local = url.hostname in {"127.0.0.1", "::1"}
        if (
            url.scheme not in {"http", "https"}
            or (url.scheme == "http" and not (local and development))
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
            or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", key_name)
            or not token.get_secret_value()
        ):
            raise ValueError("invalid reviewed key provider configuration")
        self.address, self.token, self.name = address.rstrip("/"), token, key_name

    async def request(self, path: str, payload: dict[str, str] | None = None) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=5, trust_env=False, follow_redirects=False
            ) as client:
                async with client.stream(
                    "GET" if payload is None else "POST",
                    self.address + "/v1/transit/" + path,
                    headers={"X-Vault-Token": self.token.get_secret_value()},
                    json=payload,
                ) as response:
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > 16384:
                            raise PhotoUnavailableError
                    if response.status_code != 200:
                        raise PhotoUnavailableError
                    # httpx JSON decoding is applied only to this bounded response.
                    value = httpx.Response(200, content=bytes(body)).json()
                    if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
                        raise PhotoUnavailableError
                    return cast(dict[str, Any], value["data"])
        except Exception as exc:
            raise PhotoUnavailableError("key provider unavailable") from exc

    async def validate_key(self) -> None:
        config = await self.request("keys/" + self.name)
        if (
            config.get("type") != "aes256-gcm96"
            or config.get("derived") is not True
            or config.get("exportable") is not False
            or config.get("allow_plaintext_backup") is not False
            or config.get("deletion_allowed") is not False
        ):
            raise PhotoUnavailableError("key provider policy is incompatible")

    async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
        if len(key) != 32 or not context:
            raise PhotoUnavailableError
        await self.validate_key()
        result = await self.request(
            "encrypt/" + self.name,
            {
                "plaintext": base64.b64encode(key).decode(),
                "context": base64.b64encode(context).decode(),
            },
        )
        value = result.get("ciphertext")
        if not isinstance(value, str) or not re.fullmatch(
            r"vault:v[1-9][0-9]*:[A-Za-z0-9+/=]+", value
        ):
            raise PhotoUnavailableError
        if len(value) > 4096:
            raise PhotoUnavailableError
        return self.name, value.encode("ascii")

    async def unwrap(self, key_id: str, wrapped: bytes, context: bytes) -> bytes:
        if key_id != self.name or not 1 <= len(wrapped) <= 4096 or not context:
            raise PhotoUnavailableError
        await self.validate_key()
        try:
            value = wrapped.decode("ascii")
            if not re.fullmatch(r"vault:v[1-9][0-9]*:[A-Za-z0-9+/=]+", value):
                raise ValueError
            result = await self.request(
                "decrypt/" + self.name,
                {"ciphertext": value, "context": base64.b64encode(context).decode()},
            )
            encoded = result.get("plaintext")
            if not isinstance(encoded, str) or len(encoded) > 64:
                raise ValueError
            key = base64.b64decode(encoded, validate=True)
            if len(key) != 32:
                raise ValueError
            return key
        except (UnicodeError, ValueError) as exc:
            raise PhotoUnavailableError("invalid key provider result") from exc
