"""Metadata-free query capture remains transient and can never enroll a portrait."""

import base64
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException

from accord.personas.capture_storage import validate_capture
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_contracts import RepresentationInfo
from accord.personas.face_processing import embed_face
from accord.personas.face_providers import FaceProviders
from accord.personas.face_vectors import Vectors, unit_vector
from accord.personas.photo_contracts import PhotoUpload
from accord.personas.photo_inspector import PhotoInspector
from accord.personas.repository import ConflictError
from accord.personas.service import fingerprint
from accord.personas.similarity_cache import (
    CLOSED,
    QueryStore,
    decrypt_payload,
    encrypt_payload,
    query_key,
)
from accord.personas.similarity_contracts import QueryReceipt
from accord.personas.similarity_policy import CalibrationPolicy


@dataclass(frozen=True)
class SimilarityRuntime:
    inspector: PhotoInspector
    wrapper: KeyWrapper
    faces: FaceProviders
    store: QueryStore
    policy: CalibrationPolicy | None = None


@dataclass(frozen=True)
class QueryCapture:
    receipt: QueryReceipt
    fingerprint: str
    analysis: bytes
    thumbnail: bytes


def available(runtime: SimilarityRuntime | None) -> SimilarityRuntime:
    if runtime is None or runtime.policy is None:
        raise RuntimeError("reviewed similarity runtime unavailable")
    now = datetime.now(UTC)
    if not runtime.policy.reviewed_at <= now < runtime.policy.expires_at:
        raise RuntimeError("similarity calibration outside validity window")
    return runtime


async def load_query(
    runtime: SimilarityRuntime, workspace: UUID, actor: str, query: UUID
) -> QueryCapture:
    key = query_key(workspace, actor, query)
    raw = await runtime.store.get(key)
    if raw is None or raw == CLOSED:
        raise HTTPException(410, "query expired or cleared")
    payload = await decrypt_payload(raw, key, runtime.wrapper)
    if set(payload) != {"receipt", "fingerprint", "analysis", "thumbnail"}:
        raise RuntimeError("invalid query capture")
    receipt = QueryReceipt.model_validate(payload["receipt"])
    if receipt.workspace_id != workspace or receipt.query_id != query:
        raise RuntimeError("query binding mismatch")
    if datetime.now(UTC) >= receipt.expires_at:
        raise HTTPException(410, "query expired")
    analysis, thumbnail = image_part(
        payload["analysis"], receipt.analysis_sha256, 5242880
    ), image_part(payload["thumbnail"], receipt.thumbnail_sha256, 1048576)
    intent = payload["fingerprint"]
    if not isinstance(intent, str) or len(intent) != 64:
        raise RuntimeError("invalid query fingerprint")
    return QueryCapture(receipt, intent, analysis, thumbnail)


def image_part(value: object, digest: str, maximum: int) -> bytes:
    if not isinstance(value, str):
        raise RuntimeError("invalid query image")
    data = base64.b64decode(value, validate=True)
    if (
        not 1 <= len(data) <= maximum
        or not data.startswith(b"\x89PNG\r\n\x1a\n")
        or hashlib.sha256(data).hexdigest() != digest
    ):
        raise RuntimeError("query image integrity unavailable")
    return data


async def require_query_open(
    runtime: SimilarityRuntime, workspace: UUID, actor: str, receipt: QueryReceipt
) -> None:
    raw = await runtime.store.get(query_key(workspace, actor, receipt.query_id))
    if raw is None or raw == CLOSED or datetime.now(UTC) >= receipt.expires_at:
        raise HTTPException(410, "query expired or cleared")


async def prepare_query(
    runtime: SimilarityRuntime, workspace: UUID, actor: str, command: PhotoUpload, data: bytes
) -> QueryReceipt:
    key = query_key(workspace, actor, command.request_id)
    intent = fingerprint(command.model_copy(update={"data": ""}))
    raw = await runtime.store.get(key)
    if raw is not None:
        existing = await load_query(runtime, workspace, actor, command.request_id)
        if existing.fingerprint != intent:
            raise ConflictError("query intent changed")
        return existing.receipt
    capture = await inspect_query(runtime, workspace, command, data, intent)
    payload: dict[str, object] = {
        "receipt": capture.receipt.model_dump(mode="json"),
        "fingerprint": intent,
        "analysis": base64.b64encode(capture.analysis).decode(),
        "thumbnail": base64.b64encode(capture.thumbnail).decode(),
    }
    await runtime.store.put_once(
        key, await encrypt_payload(payload, key, runtime.wrapper), capture.receipt.expires_at
    )
    chosen = await load_query(runtime, workspace, actor, command.request_id)
    if chosen.fingerprint != intent:
        raise ConflictError("query intent changed")
    return chosen.receipt


async def inspect_query(
    runtime: SimilarityRuntime, workspace: UUID, command: PhotoUpload, data: bytes, intent: str
) -> QueryCapture:
    issued = datetime.now(UTC)
    inspected = await runtime.inspector.inspect(data, command.media_type)
    validate_capture(inspected)
    p = inspected.pixels
    if (
        inspected.digest != command.sha256
        or not inspected.original_scan.engine
        or not inspected.original_scan.definitions
        or not inspected.derivative_scan.engine
        or not inspected.derivative_scan.definitions
        or not 1 <= p.width <= 320
        or not 1 <= p.height <= 320
    ):
        raise RuntimeError("invalid query inspection")
    thumb_digest = hashlib.sha256(p.thumbnail).hexdigest()
    image_part(base64.b64encode(p.thumbnail).decode(), thumb_digest, 1048576)
    detection = await runtime.faces.detector.detect(p.analysis, p.analysis_width, p.analysis_height)
    receipt = QueryReceipt(
        workspace_id=workspace,
        query_id=command.request_id,
        source_sha256=command.sha256,
        analysis_sha256=hashlib.sha256(p.analysis).hexdigest(),
        thumbnail_sha256=thumb_digest,
        width=p.analysis_width,
        height=p.analysis_height,
        detector=detection.detector,
        decoder_version=p.decoder_version,
        issued_at=issued,
        expires_at=issued + timedelta(minutes=10),
        faces=detection.faces,
        state="selection_required" if detection.faces else "no_face",
    )
    return QueryCapture(receipt, intent, p.analysis, p.thumbnail)


async def query_vectors(
    runtime: SimilarityRuntime, workspace: UUID, actor: str, capture: QueryCapture, index: int
) -> tuple[RepresentationInfo, Vectors]:
    r = capture.receipt
    key = query_key(workspace, actor, r.query_id, index + 1)
    raw = await runtime.store.get(key)
    if raw is None:
        info, vectors = await embed_face(
            capture.analysis, r.width, r.height, r.faces[index], runtime.faces
        )
        raw = await encrypt_payload(
            {"info": info.model_dump(mode="json"), "vectors": vectors}, key, runtime.wrapper
        )
        await runtime.store.put_once(key, raw, r.expires_at)
    stored = await runtime.store.get(key)
    if stored is None:
        raise HTTPException(410, "query expired")
    payload = await decrypt_payload(stored, key, runtime.wrapper)
    if set(payload) != {"info", "vectors"}:
        raise RuntimeError("invalid query representation")
    info = RepresentationInfo.model_validate(payload["info"])
    values = payload["vectors"]
    if not isinstance(values, list) or len(values) != 2:
        raise RuntimeError("invalid query vectors")
    vectors = tuple(unit_vector(v, info.dimensions) for v in values)
    await load_query(runtime, workspace, actor, r.query_id)
    return info, vectors
