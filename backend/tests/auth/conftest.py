"""Generated signing keys and transport faults exist only in isolated tests."""

import base64
import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from accord.auth.zynth_http import ZynthSettings
from accord.auth.zynth_session import ZynthSessionVerifier


def encoded(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


class SigningProvider:
    def __init__(self) -> None:
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        numbers = self.key.public_key().public_numbers()
        self.jwk = {
            "kid": "test-key",
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "n": encoded(numbers.n.to_bytes(256, "big")),
            "e": encoded(numbers.e.to_bytes(3, "big")),
        }
        self.subject, self.tenant, self.workspace = uuid4(), uuid4(), uuid4()
        self.settings = ZynthSettings(
            issuer="https://identity.example.invalid", client_id="accord-test"
        )
        self.transport, self.resolve = AsyncMock(), AsyncMock(return_value="canonical-accord-user")
        self.transport.get.side_effect = self.get
        self.status, self.profile = 200, {"sub": str(self.subject), "tid": str(self.tenant)}
        self.verifier = ZynthSessionVerifier(
            self.settings, self.transport, self.tenant, self.workspace, self.resolve
        )

    async def get(self, path: str, token: str | None = None) -> tuple[int, object]:
        if path.endswith("jwks.json"):
            return 200, {"keys": [self.jwk]}
        return self.status, self.profile

    def sign(self, body: dict[str, Any], **header: Any) -> str:
        head = {"alg": "RS256", "kid": "test-key", **header}
        message = (
            f"{encoded(json.dumps(head).encode())}.{encoded(json.dumps(body).encode())}".encode()
        )
        signature = self.key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        return f"{message.decode()}.{encoded(signature)}"

    def claims(self, **changes: Any) -> dict[str, Any]:
        now = int(datetime.now(UTC).timestamp())
        return {
            "iss": "zynth-auth",
            "aud": "zynth-services",
            "type": "access",
            "client_id": self.settings.client_id,
            "sub": str(self.subject),
            "tid": str(self.tenant),
            "sid": "human-session",
            "iat": now - 1,
            "exp": now + 300,
            **changes,
        }


@pytest.fixture
def signing() -> SigningProvider:
    return SigningProvider()
