"""Metadata-free square crop in a Linux bounded worker; no landmark alignment claim."""

import asyncio
import io
import json
import resource
import sys
from pathlib import Path

from accord.personas.face_contracts import FaceBox
from accord.personas.photo_decoder import MAX_ANALYSIS, MAX_OUTPUT, _workers


class LimitedFaceCropper:
    async def crop(self, pixels: bytes, width: int, height: int, face: FaceBox) -> bytes:
        if not 1 <= len(pixels) <= MAX_ANALYSIS:
            raise RuntimeError("invalid analysis size")
        args = [width, height, face.x, face.y, face.width, face.height]
        async with _workers:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "accord.personas.face_crop",
                json.dumps(args),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                env={"PATH": str(Path(sys.executable).parent)},
            )
            try:
                async with asyncio.timeout(10):
                    if process.stdin is None or process.stdout is None:
                        raise RuntimeError("crop worker unavailable")
                    process.stdin.write(pixels)
                    await process.stdin.drain()
                    process.stdin.close()
                    body = await process.stdout.read(MAX_OUTPUT + 1)
                    if len(body) > MAX_OUTPUT:
                        raise RuntimeError("crop worker output exceeded bound")
                    code = await process.wait()
                    if code or not body.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise RuntimeError("crop worker unavailable")
                    return body
            finally:
                if process.returncode is None:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                await process.wait()


def crop_pixels(data: bytes, args: list[int]) -> bytes:
    from PIL import Image

    if len(args) != 6 or any(type(v) is not int for v in args):
        raise ValueError("invalid crop arguments")
    width, height, x, y, fw, fh = args
    if (
        not 1 <= width <= 1024
        or not 1 <= height <= 1024
        or x < 0
        or y < 0
        or min(fw, fh) < 1
        or x + fw > width
        or y + fh > height
        or not 1 <= len(data) <= MAX_ANALYSIS
    ):
        raise ValueError("invalid crop bounds")
    Image.MAX_IMAGE_PIXELS = 1024 * 1024
    with Image.open(io.BytesIO(data), formats=["PNG"]) as image:
        if image.size != (width, height) or getattr(image, "n_frames", 1) != 1:
            raise ValueError("analysis dimensions changed")
        image.load()
        edge = max(fw, fh)
        left, top = x - (edge - fw) // 2, y - (edge - fh) // 2
        # Transparent padding avoids stretch and out-of-image coordinates.
        square = Image.new("RGBA", (edge, edge))
        right, bottom = min(width, left + edge), min(height, top + edge)
        clipped = image.crop((max(0, left), max(0, top), right, bottom)).convert("RGBA")
        square.paste(clipped, (max(0, -left), max(0, -top)))
        square.thumbnail((512, 512), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        square.save(output, "PNG")
        result = output.getvalue()
        if len(result) > MAX_OUTPUT:
            raise ValueError("crop output exceeded bound")
        return result


def worker() -> int:
    try:
        if sys.platform != "linux":
            return 78
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        if len(sys.argv) != 2:
            return 65
        data = sys.stdin.buffer.read(MAX_ANALYSIS + 1)
        result = crop_pixels(data, json.loads(sys.argv[1]))
        sys.stdout.buffer.write(result)
        return 0
    except Exception:
        return 65


if __name__ == "__main__":
    sys.exit(worker())
