"""Bounded photo decoding in an isolated worker; unavailable limits fail closed."""

import asyncio
import io
import json
import resource
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

MAX_INPUT = 10 * 1024 * 1024
MAX_OUTPUT = 1024 * 1024
MAX_ANALYSIS = 5 * 1024 * 1024
MAX_PIXELS = 8_000_000
CAPTURE_RECIPE = "rgba-png-1024-v1"
Media = Literal["image/png", "image/jpeg"]
_workers = asyncio.Semaphore(2)


@dataclass(frozen=True)
class DecodedPhoto:
    """Metadata-free PNG derivative only; no client URL, filename or scan verdict."""

    width: int
    height: int
    thumbnail: bytes
    source_width: int
    source_height: int
    orientation: int
    analysis_width: int
    analysis_height: int
    analysis: bytes
    decoder_version: str


async def limited_output(reader: asyncio.StreamReader) -> bytes:
    result = bytearray()
    while chunk := await reader.read(65_536):
        result.extend(chunk)
        if len(result) > MAX_OUTPUT + MAX_ANALYSIS:
            raise ValueError("photo derivative exceeds the limit")
    return bytes(result)


async def decode_photo(data: bytes, media: Media) -> DecodedPhoto:
    if media not in {"image/png", "image/jpeg"} or not 1 <= len(data) <= MAX_INPUT:
        raise ValueError("invalid photo size or type")
    async with _workers:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(Path(__file__).resolve()),
            media,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={},
            limit=512,
        )
        try:
            async with asyncio.timeout(10):
                if process.stdin is None or process.stdout is None:
                    raise RuntimeError("photo worker unavailable")
                process.stdin.write(data)
                await process.stdin.drain()
                process.stdin.close()
                header = await process.stdout.readline()
                body = await limited_output(process.stdout)
                code = await process.wait()
                if code == 65:
                    raise ValueError("photo could not be decoded")
                if code != 0 or len(header) > 256:
                    raise RuntimeError("photo worker unavailable")
                return decode_worker_result(header, body)
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            await process.wait()


def decode_worker_result(header: bytes, body: bytes) -> DecodedPhoto:
    value = json.loads(header)
    if (
        not isinstance(value, list)
        or len(value) != 10
        or type(value[0]) is not int
        or value[0] != 2
    ):
        raise RuntimeError("invalid photo worker result")
    _, width, height, sw, sh, orientation, aw, ah, length, release = value
    bounds = (
        (width, 320),
        (height, 320),
        (sw, 4096),
        (sh, 4096),
        (orientation, 8),
        (aw, 1024),
        (ah, 1024),
        (length, MAX_OUTPUT),
    )
    if (
        any(type(number) is not int or not 1 <= number <= bound for number, bound in bounds)
        or not isinstance(release, str)
        or not 1 <= len(release) <= 40
        or sw * sh > MAX_PIXELS
        or aw > (sh if orientation >= 5 else sw)
        or ah > (sw if orientation >= 5 else sh)
        or not length < len(body) <= length + MAX_ANALYSIS
    ):
        raise RuntimeError("invalid photo worker result")
    thumbnail, analysis = body[:length], body[length:]
    if any(not data.startswith(b"\x89PNG\r\n\x1a\n") for data in (thumbnail, analysis)):
        raise RuntimeError("invalid photo worker result")
    return DecodedPhoto(width, height, thumbnail, sw, sh, orientation, aw, ah, analysis, release)


def clean_png(image: object, edge: int, maximum: int) -> tuple[int, int, bytes]:
    from PIL import Image

    if not isinstance(image, Image.Image):
        raise ValueError("invalid pixels")
    converted = image.convert("RGBA")
    converted.thumbnail((edge, edge), Image.Resampling.LANCZOS)
    clean = Image.new("RGBA", converted.size)
    clean.paste(converted)
    output = io.BytesIO()
    clean.save(output, format="PNG")
    pixels = output.getvalue()
    if not 1 <= len(pixels) <= maximum:
        raise ValueError("photo derivative exceeds the limit")
    return clean.width, clean.height, pixels


def decode_pixels(data: bytes, media: Media) -> DecodedPhoto:
    from PIL import Image, ImageOps, PngImagePlugin, __version__

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    PngImagePlugin.MAX_TEXT_CHUNK = 256 * 1024
    PngImagePlugin.MAX_TEXT_MEMORY = 1024 * 1024
    expected = {"image/png": "PNG", "image/jpeg": "JPEG"}[media]
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data), formats=["PNG", "JPEG"]) as probe:
            if (
                probe.format != expected
                or probe.width > 4096
                or probe.height > 4096
                or probe.width * probe.height > MAX_PIXELS
                or getattr(probe, "n_frames", 1) != 1
            ):
                raise ValueError("photo is outside the allowed dimensions/type")
            probe.verify()
        with Image.open(io.BytesIO(data), formats=["PNG", "JPEG"]) as photo:
            photo.load()
            orientation = photo.getexif().get(274, 1)
            if type(orientation) is not int or not 1 <= orientation <= 8:
                raise ValueError("invalid image orientation")
            oriented = ImageOps.exif_transpose(photo)
            width, height, thumbnail = clean_png(oriented, 320, MAX_OUTPUT)
            aw, ah, analysis = clean_png(oriented, 1024, MAX_ANALYSIS)
            return DecodedPhoto(
                width,
                height,
                thumbnail,
                photo.width,
                photo.height,
                orientation,
                aw,
                ah,
                analysis,
                __version__,
            )


def worker() -> int:
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        if sys.platform != "linux":
            return 78
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        if len(sys.argv) != 2 or sys.argv[1] not in {"image/png", "image/jpeg"}:
            return 65
        media: Media = "image/png" if sys.argv[1] == "image/png" else "image/jpeg"
        data = sys.stdin.buffer.read(MAX_INPUT + 1)
        if not 1 <= len(data) <= MAX_INPUT:
            return 65
        try:
            result = decode_pixels(data, media)
        except (OSError, ValueError):
            return 65
        header = (
            json.dumps(
                [
                    2,
                    result.width,
                    result.height,
                    result.source_width,
                    result.source_height,
                    result.orientation,
                    result.analysis_width,
                    result.analysis_height,
                    len(result.thumbnail),
                    result.decoder_version,
                ]
            ).encode("ascii")
            + b"\n"
        )
        sys.stdout.buffer.write(header + result.thumbnail + result.analysis)
        return 0
    except ImportError:
        return 72
    except (OSError, ValueError, MemoryError):
        return 78
    except Exception:
        # Worker errors never echo source bytes, metadata, filenames or exception details.
        return 65


if __name__ == "__main__":
    sys.exit(worker())
