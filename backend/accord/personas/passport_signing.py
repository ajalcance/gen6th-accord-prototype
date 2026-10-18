"""Domain-separated canonical JSON and explicit owner-managed public trust keys."""

import base64
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from accord.personas.passport_contracts import Integrity, SignedPassport

DOMAIN = b"accord-persona-passport-v1\x00"
MAX_PACKAGE_BYTES = 64 * 1024


def canonical(payload: dict[str, object]) -> bytes:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    if len(encoded) > MAX_PACKAGE_BYTES:
        raise ValueError("passport exceeds the bound")
    return DOMAIN + encoded


class PassportSigner(Protocol):
    @property
    def key_id(self) -> str: ...

    async def sign(self, data: bytes) -> bytes: ...


class PassportTrust:
    """Keys come from reviewed server configuration, never from an uploaded package."""

    def __init__(self, keys: Mapping[str, Ed25519PublicKey]) -> None:
        self._keys = dict(keys)

    def contains(self, key_id: str) -> bool:
        return key_id in self._keys

    def available(self) -> bool:
        return bool(self._keys)

    def verify(self, package: SignedPassport) -> Integrity:
        key = self._keys.get(package.key_id)
        if key is None:
            return "untrusted_key"
        try:
            signature = base64.b64decode(package.signature, validate=True)
            if len(signature) != 64 or base64.b64encode(signature).decode() != package.signature:
                return "invalid_signature"
            key.verify(signature, canonical(dict(package.payload)))
        except InvalidSignature:
            return "invalid_signature"
        except (ValueError, TypeError):
            return "invalid_package"
        return "valid"


@dataclass(frozen=True)
class PassportRuntime:
    trust: PassportTrust
    signer: PassportSigner | None = None
