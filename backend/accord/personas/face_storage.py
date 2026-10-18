"""Context-bound sealed results keep boxes/vectors private and replay intent immutable."""

import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_models import PortraitCapture
from accord.personas.evidence_crypto import KeyWrapper, SealedEvidence, seal, unseal
from accord.personas.face_contracts import FaceCommand, FaceResult
from accord.personas.face_models import FaceGeneration
from accord.personas.face_vectors import Vectors, stored_vectors
from accord.personas.photo_models import Portrait


def stored_capture_context(photo: Portrait, capture: PortraitCapture) -> bytes:
    # Identical to S2 capture_context; no resealing or legacy context change.
    return json.dumps(
        [
            "accord-analysis-v1",
            str(photo.workspace_id),
            str(photo.id),
            photo.sha256,
            capture.sha256,
            capture.recipe,
            capture.decoder_version,
            capture.source_width,
            capture.source_height,
            capture.orientation,
            capture.width,
            capture.height,
            capture.scanner_engine,
            capture.scanner_definitions,
            photo.recorded_at.isoformat(),
        ],
        separators=(",", ":"),
    ).encode("ascii")


async def analysis_pixels(photo: Portrait, capture: PortraitCapture, wrapper: KeyWrapper) -> bytes:
    data = await unseal(
        SealedEvidence(capture.ciphertext, capture.nonce, capture.key_id, capture.wrapped_key),
        stored_capture_context(photo, capture),
        wrapper,
    )
    if hashlib.sha256(data).hexdigest() != capture.sha256:
        raise RuntimeError("analysis capture integrity unavailable")
    return data


def command_fingerprint(command: FaceCommand) -> str:
    return hashlib.sha256(command.model_dump_json().encode()).hexdigest()


def generation_context(row: FaceGeneration) -> bytes:
    return json.dumps(
        [
            "accord-face-generation-v1",
            str(row.workspace_id),
            str(row.id),
            str(row.version_id),
            str(row.portrait_id),
            str(row.request_id),
            row.actor_ref,
            row.fingerprint,
            row.recorded_at.isoformat(),
        ],
        separators=(",", ":"),
    ).encode("ascii")


async def load_result(row: FaceGeneration, wrapper: KeyWrapper) -> FaceResult:
    result, _vectors = await load_generation(row, wrapper)
    return result


async def load_generation(row: FaceGeneration, wrapper: KeyWrapper) -> tuple[FaceResult, Vectors]:
    data = await unseal(
        SealedEvidence(row.ciphertext, row.nonce, row.key_id, row.wrapped_key),
        generation_context(row),
        wrapper,
    )
    if len(data) > 131072:
        raise RuntimeError("invalid face generation size")
    payload = json.loads(data)
    if not isinstance(payload, dict) or set(payload) != {"result", "vectors"}:
        raise RuntimeError("invalid sealed face generation")
    result = FaceResult.model_validate(payload["result"])
    if (
        result.workspace_id != row.workspace_id
        or result.generation_id != row.id
        or result.version_id != row.version_id
        or result.portrait_id != row.portrait_id
        or result.request_id != row.request_id
        or result.recorded_at != row.recorded_at
    ):
        raise RuntimeError("face generation context mismatch")
    return result, stored_vectors(result, payload["vectors"])


async def store_result(
    session: AsyncSession,
    result: FaceResult,
    command: FaceCommand,
    actor: str,
    vectors: tuple[tuple[float, ...], ...],
    wrapper: KeyWrapper,
) -> None:
    stored_vectors(result, vectors)
    row = FaceGeneration(
        id=result.generation_id,
        workspace_id=result.workspace_id,
        version_id=result.version_id,
        portrait_id=result.portrait_id,
        request_id=command.request_id,
        actor_ref=actor,
        fingerprint=command_fingerprint(command),
        recorded_at=result.recorded_at,
    )
    data = json.dumps(
        {"result": result.model_dump(mode="json"), "vectors": vectors},
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    if len(data) > 131072:
        raise RuntimeError("face generation exceeds storage bound")
    sealed = await seal(data, generation_context(row), wrapper)
    row.ciphertext, row.nonce = sealed.ciphertext, sealed.nonce
    row.key_id, row.wrapped_key = sealed.key_id, sealed.wrapped_key
    session.add(row)
