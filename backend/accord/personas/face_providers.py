"""Injected providers only: no downloaded weights, credential discovery or synthetic fallback."""

import math
from dataclasses import dataclass
from typing import Protocol

from accord.personas.face_contracts import FaceBox


@dataclass(frozen=True)
class Detection:
    detector: str
    faces: tuple[FaceBox, ...]


@dataclass(frozen=True)
class Embedding:
    model: str
    revision: str
    values: tuple[float, ...]


class FaceDetector(Protocol):
    async def detect(self, pixels: bytes, width: int, height: int) -> Detection: ...


class ImageEncoder(Protocol):
    async def encode(self, pixels: bytes) -> Embedding: ...


class FaceCropper(Protocol):
    async def crop(self, pixels: bytes, width: int, height: int, face: FaceBox) -> bytes: ...


@dataclass(frozen=True)
class FaceProviders:
    detector: FaceDetector
    encoder: ImageEncoder
    cropper: FaceCropper


def normalized(embedding: Embedding) -> tuple[float, ...]:
    values = embedding.values
    if (
        not embedding.model
        or len(embedding.model) > 160
        or not embedding.revision
        or len(embedding.revision) > 160
        or not 1 <= len(values) <= 1408
        or any(type(v) not in (float, int) or not math.isfinite(v) for v in values)
    ):
        raise RuntimeError("invalid embedding contract")
    norm = math.hypot(*values)
    if not math.isfinite(norm) or norm <= 0:
        raise RuntimeError("invalid embedding norm")
    return tuple(v / norm for v in values)


def quality_reasons(face: FaceBox) -> tuple[str, ...]:
    """Conservative provisional eligibility, explicitly uncalibrated until held-out evaluation."""
    reasons: list[str] = []
    if min(face.width, face.height) < 64:
        reasons.append("small_face")
    if face.confidence < 0.8:
        reasons.append("low_detection_confidence")
    if abs(face.yaw) > 45 or abs(face.pitch) > 30:
        reasons.append("extreme_pose")
    if face.blur in {"LIKELY", "VERY_LIKELY"}:
        reasons.append("blur")
    return tuple(reasons)
