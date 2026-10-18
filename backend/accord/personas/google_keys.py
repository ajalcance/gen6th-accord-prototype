"""KMS envelope wrapping with context/CRC integrity and explicitly retained legacy keys."""

import base64
import hashlib
import re

from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_google import GoogleTransport
from accord.personas.passport_google import crc32c


def key_version(value: str) -> str:
    if len(value) > 240 or not re.fullmatch(
        r"projects/[a-z][a-z0-9-]{4,61}[a-z0-9]/locations/[a-z0-9-]{1,63}/"
        r"keyRings/[A-Za-z0-9_-]{1,63}/cryptoKeys/[A-Za-z0-9_-]{1,63}/"
        r"cryptoKeyVersions/[1-9][0-9]{0,9}",
        value,
    ):
        raise ValueError("immutable KMS key version required")
    return value


def key_alias(value: str) -> str:
    return "gcp-kms-v1:" + hashlib.sha256(key_version(value).encode()).hexdigest()


def checked_bytes(response: dict[str, object], field: str, maximum: int) -> bytes:
    encoded, checksum = response.get(field), response.get(field + "Crc32c")
    if not isinstance(encoded, str) or len(encoded) > maximum * 2:
        raise RuntimeError("invalid KMS response")
    data = base64.b64decode(encoded, validate=True)
    if (
        not 1 <= len(data) <= maximum
        or not isinstance(checksum, str)
        or not checksum.isascii()
        or not checksum.isdigit()
        or len(checksum) > 10
        or crc32c(data) != int(checksum)
    ):
        raise RuntimeError("KMS response integrity unavailable")
    return data


class GoogleKeyWrapper:
    def __init__(self, primary: str, retained: tuple[str, ...], transport: GoogleTransport) -> None:
        self.primary, self.transport = key_version(primary), transport
        self.keys = {key_alias(v): key_version(v) for v in (primary, *retained)}

    async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
        if len(key) != 32 or not 1 <= len(context) <= 8192:
            raise RuntimeError("invalid KMS wrapping input")
        response = await self.transport.post(
            f"https://cloudkms.googleapis.com/v1/{self.primary}:encrypt",
            self.primary.split("/")[1],
            {
                "plaintext": base64.b64encode(key).decode(),
                "additionalAuthenticatedData": base64.b64encode(context).decode(),
                "plaintextCrc32c": str(crc32c(key)),
                "additionalAuthenticatedDataCrc32c": str(crc32c(context)),
            },
        )
        if (
            response.get("name") != self.primary
            or response.get("verifiedPlaintextCrc32c") is not True
            or response.get("verifiedAdditionalAuthenticatedDataCrc32c") is not True
        ):
            raise RuntimeError("KMS wrapping integrity unavailable")
        return key_alias(self.primary), checked_bytes(response, "ciphertext", 4096)

    async def unwrap(self, key_id: str, wrapped: bytes, context: bytes) -> bytes:
        version = self.keys.get(key_id)
        if version is None or not 1 <= len(wrapped) <= 4096 or not 1 <= len(context) <= 8192:
            raise RuntimeError("KMS key unavailable")
        resource = version.rsplit("/cryptoKeyVersions/", 1)[0]
        response = await self.transport.post(
            f"https://cloudkms.googleapis.com/v1/{resource}:decrypt",
            version.split("/")[1],
            {
                "ciphertext": base64.b64encode(wrapped).decode(),
                "additionalAuthenticatedData": base64.b64encode(context).decode(),
                "ciphertextCrc32c": str(crc32c(wrapped)),
                "additionalAuthenticatedDataCrc32c": str(crc32c(context)),
            },
        )
        key = checked_bytes(response, "plaintext", 32)
        if len(key) != 32:
            raise RuntimeError("invalid unwrapped key")
        return key


class RetainedKeyWrapper:
    def __init__(self, current: GoogleKeyWrapper, legacy: KeyWrapper | None) -> None:
        self.current, self.legacy = current, legacy

    async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
        return await self.current.wrap(key, context)

    async def unwrap(self, key_id: str, wrapped: bytes, context: bytes) -> bytes:
        if key_id.startswith("gcp-kms-v1:"):
            return await self.current.unwrap(key_id, wrapped, context)
        if self.legacy is None:
            raise RuntimeError("legacy key unavailable")
        return await self.legacy.unwrap(key_id, wrapped, context)
