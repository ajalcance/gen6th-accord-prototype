"""Actual crop/AES behavior with explicitly synthetic detector and vector fixtures."""

import io
from uuid import uuid4

import pytest
from PIL import Image, PngImagePlugin
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.face_contracts import FaceBox, FaceCommand, FaceResult
from accord.personas.face_crop import crop_pixels
from accord.personas.face_models import FaceGeneration
from accord.personas.face_processing import detect_result, selected_result
from accord.personas.face_providers import Detection, Embedding, FaceProviders, normalized
from accord.personas.face_storage import load_result, store_result
from personas.test_photo_storage import FixtureWrapper


def image_bytes() -> bytes:
    stream = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("private-source-note", "fixture")
    Image.new("RGBA", (200, 100), "red").save(stream, "PNG", pnginfo=metadata)
    return stream.getvalue()


def face(**changes: object) -> FaceBox:
    return FaceBox.model_validate(
        {
            "index": 0,
            "x": 10,
            "y": 10,
            "width": 80,
            "height": 80,
            "confidence": 0.95,
            "yaw": 0.0,
            "pitch": 0.0,
            "blur": "UNLIKELY",
            **changes,
        }
    )


class SyntheticProviders:
    calls: list[bytes]

    def __init__(self, faces: tuple[FaceBox, ...] = (face(),)) -> None:
        self.faces, self.calls = faces, []

    async def detect(self, pixels: bytes, width: int, height: int) -> Detection:
        return Detection("synthetic-detector", self.faces)

    async def encode(self, pixels: bytes) -> Embedding:
        self.calls.append(pixels)
        return Embedding("synthetic-encoder", "fixture-v1", (3.0, 4.0))

    async def crop(self, pixels: bytes, width: int, height: int, box: FaceBox) -> bytes:
        return crop_pixels(pixels, [width, height, box.x, box.y, box.width, box.height])

    def providers(self) -> FaceProviders:
        return FaceProviders(self, self, self)


@pytest.mark.asyncio
async def test_explicit_selection_real_crop_normalization_and_encrypted_receipt() -> None:
    pixels, synthetic, workspace = image_bytes(), SyntheticProviders(), uuid4()
    command = FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4())
    detected = await detect_result(
        workspace, command, pixels, "a" * 64, 200, 100, synthetic.providers()
    )
    assert detected.state == "selection_required" and not synthetic.calls
    selected = command.model_copy(
        update={"request_id": uuid4(), "generation_id": detected.generation_id, "face_index": 0}
    )
    result, vectors = await selected_result(selected, detected, pixels, synthetic.providers())
    assert vectors == ((0.6, 0.8), (0.6, 0.8)) and result.parent_id == detected.generation_id
    with Image.open(io.BytesIO(synthetic.calls[0])) as crop:
        assert crop.size == (80, 80) and not crop.info
    assert synthetic.calls[1] == pixels
    wrapper = FixtureWrapper()
    async with AsyncSession() as session:
        await store_result(session, result, selected, "creator-a", vectors, wrapper)
        row = next(value for value in session.new if isinstance(value, FaceGeneration))
        assert b"synthetic-encoder" not in row.ciphertext
        assert await load_result(row, wrapper) == result
        row.version_id = uuid4()
        with pytest.raises(AssertionError):
            await load_result(row, wrapper)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"width": 32}, "small_face"),
        ({"confidence": 0.5}, "low_detection_confidence"),
        ({"yaw": 60.0}, "extreme_pose"),
        ({"blur": "LIKELY"}, "blur"),
    ],
)
async def test_quality_block_never_calls_crop_encoder(
    changes: dict[str, object], reason: str
) -> None:
    synthetic = SyntheticProviders((face(**changes),))
    command = FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4())
    parent = await detect_result(
        uuid4(), command, image_bytes(), "a" * 64, 200, 100, synthetic.providers()
    )
    command = command.model_copy(update={"generation_id": parent.generation_id, "face_index": 0})
    result, vectors = await selected_result(command, parent, image_bytes(), synthetic.providers())
    assert result.state == "quality_blocked" and reason in result.reasons
    assert not vectors and not synthetic.calls


@pytest.mark.asyncio
async def test_no_face_and_outside_box_never_become_representation() -> None:
    command = FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4())
    empty = SyntheticProviders(())
    result = await detect_result(
        uuid4(), command, image_bytes(), "a" * 64, 200, 100, empty.providers()
    )
    assert result.state == "no_face" and not empty.calls
    with pytest.raises(ValidationError):
        FaceResult.model_validate(
            {**result.model_dump(), "faces": (face(x=150),), "state": "selection_required"}
        )
    with pytest.raises(ValidationError):
        FaceCommand(version_id=uuid4(), portrait_id=uuid4(), request_id=uuid4(), face_index=0)


@pytest.mark.parametrize(
    "values", [(0.0, 0.0), (float("nan"), 1.0), (float("inf"), 1.0), (True, 1.0)]
)
def test_nonfinite_zero_and_boolean_vectors_rejected(values: tuple[float, ...]) -> None:
    with pytest.raises(RuntimeError):
        normalized(Embedding("fixture", "v1", values))


@pytest.mark.parametrize(
    "args", [[201, 100, 10, 10, 80, 80], [200, 100, -1, 10, 80, 80], [200, 100, 190, 10, 80, 80]]
)
def test_crop_dimensions_and_bounds_are_verified(args: list[int]) -> None:
    with pytest.raises(ValueError):
        crop_pixels(image_bytes(), args)
