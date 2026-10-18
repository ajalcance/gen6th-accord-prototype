"""Explicit detector -> stored face selection -> provisional quality -> dual representation."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

from accord.personas.face_contracts import FaceBox, FaceCommand, FaceResult, RepresentationInfo
from accord.personas.face_providers import FaceProviders, normalized, quality_reasons


async def detect_result(
    workspace: UUID,
    command: FaceCommand,
    pixels: bytes,
    digest: str,
    width: int,
    height: int,
    providers: FaceProviders,
) -> FaceResult:
    detection = await providers.detector.detect(pixels, width, height)
    return FaceResult(
        workspace_id=workspace,
        **command.model_dump(include={"version_id", "portrait_id", "request_id"}),
        generation_id=uuid4(),
        parent_id=None,
        source_sha256=digest,
        width=width,
        height=height,
        detector=detection.detector,
        recorded_at=datetime.now(UTC),
        faces=detection.faces,
        selected=None,
        state="selection_required" if detection.faces else "no_face",
        reasons=(),
        representation=None,
    )


async def selected_result(
    command: FaceCommand, parent: FaceResult, pixels: bytes, providers: FaceProviders
) -> tuple[FaceResult, tuple[tuple[float, ...], ...]]:
    if (
        parent.state != "selection_required"
        or command.face_index is None
        or command.face_index >= len(parent.faces)
    ):
        raise ValueError("select a face from a stored detection generation")
    face = parent.faces[command.face_index]
    reasons = quality_reasons(face)
    info: RepresentationInfo | None = None
    vectors: tuple[tuple[float, ...], ...] = ()
    if not reasons:
        info, vectors = await embed_face(pixels, parent.width, parent.height, face, providers)
    return selection_receipt(command, parent, reasons, info), vectors


async def embed_face(
    pixels: bytes, width: int, height: int, face: FaceBox, providers: FaceProviders
) -> tuple[RepresentationInfo, tuple[tuple[float, ...], ...]]:
    crop = await providers.cropper.crop(pixels, width, height, face)
    if not 1 <= len(crop) <= 1048576 or not crop.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("invalid crop provider result")
    face_embedding = await providers.encoder.encode(crop)
    whole_embedding = await providers.encoder.encode(pixels)
    if (
        face_embedding.model != whole_embedding.model
        or face_embedding.revision != whole_embedding.revision
        or len(face_embedding.values) != len(whole_embedding.values)
    ):
        raise RuntimeError("incompatible representation generations")
    vectors = (normalized(face_embedding), normalized(whole_embedding))
    return (
        RepresentationInfo(
            model=face_embedding.model,
            provider_revision=face_embedding.revision,
            dimensions=len(vectors[0]),
            crop_sha256=hashlib.sha256(crop).hexdigest(),
        ),
        vectors,
    )


def selection_receipt(
    command: FaceCommand,
    parent: FaceResult,
    reasons: tuple[str, ...],
    info: RepresentationInfo | None,
) -> FaceResult:
    payload = parent.model_dump(
        exclude={
            "request_id",
            "generation_id",
            "parent_id",
            "recorded_at",
            "selected",
            "state",
            "reasons",
            "representation",
        }
    )
    return FaceResult(
        **payload,
        request_id=command.request_id,
        generation_id=uuid4(),
        parent_id=parent.generation_id,
        recorded_at=datetime.now(UTC),
        selected=command.face_index,
        state="quality_blocked" if reasons else "represented",
        reasons=reasons,
        representation=info,
    )
