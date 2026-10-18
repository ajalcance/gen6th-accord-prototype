"""RS256 access-token validation using existing cryptography; no token-type fallback."""

import base64
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from pydantic import AwareDatetime, BaseModel, ConfigDict

from accord.auth.zynth_http import ZynthSettings


class InvalidZynthTokenError(Exception):
    """A token cannot establish an authenticated human."""


class AccessIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    subject: UUID
    tenant: UUID
    session_id: str
    issued_at: AwareDatetime
    expires_at: AwareDatetime


def decode_segment(value: str) -> bytes:
    if not value or any(
        c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in value
    ):
        raise InvalidZynthTokenError
    return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise InvalidZynthTokenError
        result[name] = value
    return result


def token_parts(token: str) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    try:
        if len(token) > 16_384:
            raise InvalidZynthTokenError
        header, payload, signature = token.split(".")
        head = json.loads(decode_segment(header), object_pairs_hook=unique_object)
        body = json.loads(decode_segment(payload), object_pairs_hook=unique_object)
        if (
            not isinstance(head, dict)
            or not isinstance(body, dict)
            or head.get("alg") != "RS256"
            or not isinstance(head.get("kid"), str)
            or not head["kid"]
            or len(head["kid"]) > 128
            or any(key in head for key in ("crit", "jku", "jwk", "x5u"))
        ):
            raise InvalidZynthTokenError
        return head, body, f"{header}.{payload}".encode("ascii"), decode_segment(signature)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise InvalidZynthTokenError from exc


def verify_signature(key: dict[str, Any], message: bytes, signature: bytes) -> None:
    try:
        if (
            key.get("kty") != "RSA"
            or key.get("use", "sig") != "sig"
            or key.get("alg", "RS256") != "RS256"
            or not isinstance(key.get("n"), str)
            or not isinstance(key.get("e"), str)
            or len(key["n"]) > 1366
            or len(key["e"]) > 8
        ):
            raise InvalidZynthTokenError
        numbers = rsa.RSAPublicNumbers(
            int.from_bytes(decode_segment(key["e"]), "big"),
            int.from_bytes(decode_segment(key["n"]), "big"),
        )
        public = numbers.public_key()
        if not 2048 <= public.key_size <= 8192:
            raise InvalidZynthTokenError
        public.verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
    except (KeyError, ValueError, TypeError, InvalidSignature) as exc:
        raise InvalidZynthTokenError from exc


def verified_claims(body: dict[str, Any], settings: ZynthSettings) -> AccessIdentity:
    try:
        now = datetime.now(UTC).timestamp()
        if (
            body.get("iss") != "zynth-auth"
            or body.get("aud") != settings.audience
            or body.get("type") != "access"
            or body.get("client_id") != settings.client_id
            or body.get("actor") not in (None, "user")
            or "cnf" in body
            or type(body.get("iat")) is not int
            or type(body.get("exp")) is not int
            or not body["iat"] <= now < body["exp"]
            or body["exp"] <= body["iat"]
            or not isinstance(body.get("sid"), str)
            or not 1 <= len(body["sid"]) <= 64
            or ("nbf" in body and (type(body["nbf"]) is not int or body["nbf"] > now))
        ):
            raise InvalidZynthTokenError
        return AccessIdentity(
            subject=UUID(body["sub"]),
            tenant=UUID(body["tid"]),
            session_id=body["sid"],
            issued_at=datetime.fromtimestamp(body["iat"], UTC),
            expires_at=datetime.fromtimestamp(body["exp"], UTC),
        )
    except (KeyError, ValueError, TypeError, OverflowError, OSError) as exc:
        raise InvalidZynthTokenError from exc
