"""Prepared Cloud KMS Ed25519 signing; workload access and trust key activation are explicit."""

import base64
import binascii
import re

from accord.personas.face_google import GoogleTransport, project_id
from accord.personas.passport_signing import MAX_PACKAGE_BYTES


def crc32c(data: bytes) -> int:
    checksum = 0xFFFFFFFF
    for byte in data:
        checksum ^= byte
        for _ in range(8):
            checksum = (checksum >> 1) ^ (0x82F63B78 if checksum & 1 else 0)
    return checksum ^ 0xFFFFFFFF


class GooglePassportSigner:
    """Use an owner-selected EC_SIGN_ED25519 software key version, never a mutable alias."""

    def __init__(self, key_id: str, transport: GoogleTransport) -> None:
        match = re.fullmatch(
            r"projects/([a-z][a-z0-9-]{4,61}[a-z0-9])/locations/([a-z0-9-]{1,63})/"
            r"keyRings/([A-Za-z0-9_-]{1,63})/cryptoKeys/([A-Za-z0-9_-]{1,63})/"
            r"cryptoKeyVersions/([1-9][0-9]{0,9})",
            key_id,
        )
        if match is None or len(key_id) > 240:
            raise ValueError("invalid immutable KMS key version")
        self._key_id, self.project = key_id, project_id(match.group(1))
        self.transport = transport

    @property
    def key_id(self) -> str:
        return self._key_id

    async def sign(self, data: bytes) -> bytes:
        if not data or len(data) > MAX_PACKAGE_BYTES:
            raise RuntimeError("invalid passport signing input")
        response = await self.transport.post(
            f"https://cloudkms.googleapis.com/v1/{self.key_id}:asymmetricSign",
            self.project,
            {"data": base64.b64encode(data).decode(), "dataCrc32c": str(crc32c(data))},
        )
        try:
            encoded = response.get("signature")
            checksum = response.get("signatureCrc32c")
            if (
                response.get("name") != self.key_id
                or response.get("verifiedDataCrc32c") is not True
                or not isinstance(encoded, str)
                or len(encoded) != 88
                or not isinstance(checksum, str)
                or not checksum.isascii()
                or not checksum.isdigit()
                or len(checksum) > 10
            ):
                raise ValueError("incomplete KMS integrity result")
            signature = base64.b64decode(encoded, validate=True)
            if len(signature) != 64 or crc32c(signature) != int(checksum):
                raise ValueError("KMS response integrity mismatch")
        except (ValueError, binascii.Error) as exc:
            raise RuntimeError("KMS signing is unavailable") from exc
        return signature
