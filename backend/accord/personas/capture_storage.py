"""Encrypt dedicated analysis pixels with their immutable source and processing context."""

import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_models import PortraitCapture
from accord.personas.evidence_crypto import KeyWrapper, seal
from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_decoder import CAPTURE_RECIPE, MAX_ANALYSIS, MAX_PIXELS
from accord.personas.photo_inspector import InspectedPhoto
from accord.personas.photo_models import Portrait


def validate_capture(inspected: InspectedPhoto) -> None:
    pixels, scan = inspected.pixels, inspected.analysis_scan
    sw, sh = pixels.source_width, pixels.source_height
    oriented = (sh, sw) if pixels.orientation >= 5 else (sw, sh)
    if (
        scan is None
        or not scan.engine
        or not scan.definitions
        or not pixels.decoder_version
        or not 1 <= pixels.source_width <= 4096
        or not 1 <= pixels.source_height <= 4096
        or pixels.source_width * pixels.source_height > MAX_PIXELS
        or not 1 <= pixels.orientation <= 8
        or not 1 <= pixels.analysis_width <= 1024
        or not 1 <= pixels.analysis_height <= 1024
        or pixels.analysis_width > oriented[0]
        or pixels.analysis_height > oriented[1]
        or not 1 <= len(pixels.analysis) <= MAX_ANALYSIS
        or not pixels.analysis.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise PhotoUnavailableError("invalid analysis capture")


def capture_context(row: Portrait, digest: str, inspected: InspectedPhoto) -> bytes:
    pixels, scan = inspected.pixels, inspected.analysis_scan
    if scan is None:
        raise PhotoUnavailableError("analysis scan unavailable")
    return json.dumps(
        [
            "accord-analysis-v1",
            str(row.workspace_id),
            str(row.id),
            row.sha256,
            digest,
            CAPTURE_RECIPE,
            pixels.decoder_version,
            pixels.source_width,
            pixels.source_height,
            pixels.orientation,
            pixels.analysis_width,
            pixels.analysis_height,
            scan.engine,
            scan.definitions,
            row.recorded_at.isoformat(),
        ],
        separators=(",", ":"),
    ).encode("ascii")


async def store_capture(
    session: AsyncSession, row: Portrait, inspected: InspectedPhoto, wrapper: KeyWrapper
) -> None:
    validate_capture(inspected)
    pixels, scan = inspected.pixels, inspected.analysis_scan
    if scan is None:
        raise PhotoUnavailableError("analysis scan unavailable")
    digest = hashlib.sha256(pixels.analysis).hexdigest()
    sealed = await seal(pixels.analysis, capture_context(row, digest, inspected), wrapper)
    session.add(
        PortraitCapture(
            portrait_id=row.id,
            workspace_id=row.workspace_id,
            source_width=pixels.source_width,
            source_height=pixels.source_height,
            orientation=pixels.orientation,
            width=pixels.analysis_width,
            height=pixels.analysis_height,
            sha256=digest,
            recipe=CAPTURE_RECIPE,
            decoder_version=pixels.decoder_version,
            scanner_engine=scan.engine,
            scanner_definitions=scan.definitions,
            recorded_at=row.recorded_at,
            ciphertext=sealed.ciphertext,
            nonce=sealed.nonce,
            key_id=sealed.key_id,
            wrapped_key=sealed.wrapped_key,
        )
    )
