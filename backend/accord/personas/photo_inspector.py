"""Original and generated pixels must both pass a current malware inspection."""

import hashlib
from dataclasses import dataclass
from typing import Protocol

from accord.personas.photo_contracts import PhotoRejectedError, PhotoUnavailableError
from accord.personas.photo_decoder import DecodedPhoto, Media, decode_photo
from accord.personas.photo_scanner import PhotoScanner, ScanReceipt


@dataclass(frozen=True)
class InspectedPhoto:
    pixels: DecodedPhoto
    original_scan: ScanReceipt
    derivative_scan: ScanReceipt
    digest: str
    analysis_scan: ScanReceipt | None = None


class PhotoInspector(Protocol):
    async def inspect(self, data: bytes, media: Media) -> InspectedPhoto: ...


class PillowClamdInspector:
    def __init__(self, scanner: PhotoScanner) -> None:
        self.scanner = scanner

    async def inspect(self, data: bytes, media: Media) -> InspectedPhoto:
        original = await self.scanner.scan(data)
        try:
            pixels = await decode_photo(data, media)
        except ValueError as exc:
            raise PhotoRejectedError("photo cannot be decoded") from exc
        except Exception as exc:
            raise PhotoUnavailableError("decoder unavailable") from exc
        derivative = await self.scanner.scan(pixels.thumbnail)
        analysis = await self.scanner.scan(pixels.analysis)
        return InspectedPhoto(
            pixels, original, derivative, hashlib.sha256(data).hexdigest(), analysis
        )
