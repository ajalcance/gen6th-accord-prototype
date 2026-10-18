"""Bounded private document inspection reusing the reviewed image and clamd adapters."""

import hashlib
from datetime import UTC, datetime

from accord.personas.evidence_contracts import MAX_EVIDENCE_BYTES, Inspection, MediaType
from accord.personas.photo_contracts import PhotoRejectedError
from accord.personas.photo_inspector import PhotoInspector
from accord.personas.photo_scanner import PhotoScanner


class DocumentInspector:
    def __init__(self, images: PhotoInspector, scanner: PhotoScanner) -> None:
        self.images, self.scanner = images, scanner

    async def inspect(self, data: bytes) -> Inspection:
        if not 1 <= len(data) <= MAX_EVIDENCE_BYTES:
            raise ValueError("invalid evidence size")
        media: MediaType = "text/plain"
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            media = "image/png"
        elif data.startswith(b"\xff\xd8\xff"):
            media = "image/jpeg"
        if media == "text/plain":
            try:
                text = data.decode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise PhotoRejectedError("use UTF-8 text, PNG or JPEG") from exc
            if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
                raise PhotoRejectedError("binary control bytes are not text evidence")
            receipt = await self.scanner.scan(data)
        else:
            result = await self.images.inspect(data, media)
            receipt = result.original_scan
        return Inspection(
            sha256=hashlib.sha256(data).hexdigest(),
            byte_length=len(data),
            detected_type=media,
            verdict="clean",
            engine=receipt.engine,
            definitions=receipt.definitions,
            inspected_at=datetime.now(UTC),
        )
