"""Real pixel tests and worker fail-closed tests; no SQL, app settings or private images."""

import io
import sys

import pytest
from PIL import Image, PngImagePlugin

from accord.personas.photo_decoder import MAX_INPUT, Media, decode_photo, decode_pixels, worker


def image_bytes(kind: str = "PNG", width: int = 640, height: int = 320) -> bytes:
    output = io.BytesIO()
    image = Image.new("RGB", (width, height), (24, 38, 51))
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("private-description", "synthetic source metadata")
    image.save(output, format=kind, **({"pnginfo": metadata} if kind == "PNG" else {}))
    return output.getvalue()


@pytest.mark.parametrize("kind,media", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_real_pixels_are_bounded_and_metadata_free(kind: str, media: Media) -> None:
    result = decode_pixels(image_bytes(kind), media)
    assert (result.width, result.height) == (320, 160)
    with Image.open(io.BytesIO(result.thumbnail)) as thumbnail:
        thumbnail.load()
        assert thumbnail.format == "PNG"
        assert not thumbnail.info


@pytest.mark.parametrize("data,media", [(b"invalid", "image/png"), (image_bytes(), "image/jpeg")])
def test_malformed_and_mismatched_types_are_rejected(data: bytes, media: Media) -> None:
    with pytest.raises((OSError, ValueError)):
        decode_pixels(data, media)


def test_dimensions_animation_and_truncation_are_rejected() -> None:
    animated = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        animated,
        format="PNG",
        save_all=True,
        append_images=[Image.new("RGB", (2, 2), "blue")],
    )
    for data in (image_bytes(width=4097), animated.getvalue(), image_bytes()[:30]):
        with pytest.raises((OSError, ValueError)):
            decode_pixels(data, "image/png")


@pytest.mark.asyncio
async def test_input_size_is_rejected_before_a_worker() -> None:
    with pytest.raises(ValueError, match="size"):
        await decode_photo(b"x" * (MAX_INPUT + 1), "image/png")


@pytest.mark.asyncio
async def test_real_worker_is_bounded_or_explicitly_unavailable() -> None:
    if sys.platform != "linux":
        with pytest.raises(RuntimeError, match="unavailable"):
            await decode_photo(image_bytes(), "image/png")
    else:
        result = await decode_photo(image_bytes(), "image/png")
        assert result.width == 320


def test_resource_setup_failure_is_unavailable_not_an_invalid_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failure(*_args: object) -> None:
        raise ValueError("synthetic unavailable resource limit")

    monkeypatch.setattr("accord.personas.photo_decoder.resource.setrlimit", failure)
    assert worker() == 78
