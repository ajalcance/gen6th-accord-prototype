"""Private quarantine services; providers and retention authority are explicitly injected."""

import asyncio
import hashlib
from collections.abc import AsyncIterable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_contracts import EvidenceIntent, EvidenceSnapshot, Inspection
from accord.personas.evidence_crypto import KeyWrapper, binding, seal
from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence
from accord.personas.evidence_repository import (
    inspection,
    observed,
    owned,
    payload,
    plaintext,
    snapshot,
)
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_repository import authorize_actor, locked_version, require_current


class ContentInspector(Protocol):
    async def inspect(self, data: bytes) -> Inspection:
        """Full bounded media decoding plus malware inspection; errors never mean clean."""
        ...


class RetentionGate(Protocol):
    async def may_purge(self, workspace_id: UUID, evidence_id: UUID) -> bool:
        """Trusted hold/retention check; unavailable or ambiguous state must deny deletion."""
        ...


async def collect(chunks: AsyncIterable[bytes], intent: EvidenceIntent) -> bytes:
    """Bound even chunked input without trusting Content-Length or retaining filenames."""
    result = bytearray()
    async with asyncio.timeout(30):
        async for chunk in chunks:
            if len(result) + len(chunk) > intent.byte_length:
                raise ValueError("evidence exceeds declared size")
            result.extend(chunk)
    data = bytes(result)
    if len(data) != intent.byte_length or hashlib.sha256(data).hexdigest() != intent.sha256:
        raise ValueError("evidence bytes disagree with intent")
    return data


async def enqueue(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    intent: EvidenceIntent,
    chunks: AsyncIterable[bytes],
    wrapper: KeyWrapper,
) -> EvidenceSnapshot:
    """Authorize before consuming bytes; commit ciphertext and server observation together."""
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, intent.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace_id, actor, "creator")
        version, persona = await locked_version(session, workspace_id, intent.version_id)
        if persona.owner_ref != actor.actor_ref:
            raise AccessDeniedError("private evidence access denied")
        existing = await session.scalar(
            select(PrivateEvidence).where(
                PrivateEvidence.workspace_id == workspace_id,
                PrivateEvidence.owner_ref == actor.actor_ref,
                PrivateEvidence.request_id == intent.request_id,
            )
        )
        data = await collect(chunks, intent)
        if existing is not None:
            if existing.fingerprint != fingerprint(intent):
                raise ConflictError("evidence request ID already used")
            scanned = await inspection(session, existing)
            result = snapshot(existing, scanned.verdict if scanned else None)
        else:
            require_current(version, persona)
            row, stored = await new_evidence(workspace_id, actor, intent, data, wrapper)
            session.add(row)
            await session.flush()
            session.add(stored)
            session.add(observed(row, actor, intent.request_id, "persona.evidence_quarantined"))
            result = snapshot(row)
        await authorize_actor(session, workspace_id, actor, "creator")
    return result


async def new_evidence(
    workspace_id: UUID,
    actor: WorkflowActor,
    intent: EvidenceIntent,
    data: bytes,
    wrapper: KeyWrapper,
) -> tuple[PrivateEvidence, EvidencePayload]:
    evidence_id, now = uuid4(), datetime.now(UTC)
    context = binding(workspace_id, intent.version_id, evidence_id, intent.sha256)
    async with asyncio.timeout(10):
        encrypted = await seal(data, context, wrapper)
    row = PrivateEvidence(
        id=evidence_id,
        workspace_id=workspace_id,
        owner_ref=actor.actor_ref,
        fingerprint=fingerprint(intent),
        recorded_at=now,
        expires_at=now + timedelta(days=7),
        **intent.model_dump(),
    )
    stored = EvidencePayload(
        evidence_id=evidence_id,
        workspace_id=workspace_id,
        ciphertext=encrypted.ciphertext,
        nonce=encrypted.nonce,
        key_id=encrypted.key_id,
        wrapped_key=encrypted.wrapped_key,
    )
    return row, stored


def validate_inspection(row: PrivateEvidence, result: Inspection) -> None:
    now = datetime.now(UTC)
    if (
        result.sha256 != row.sha256
        or result.byte_length != row.byte_length
        or result.detected_type != row.media_type
        or not row.recorded_at <= result.inspected_at <= now
        or now >= row.expires_at
    ):
        raise ValueError("inspection does not bind the declared evidence")


async def inspect_evidence(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    evidence_id: UUID,
    wrapper: KeyWrapper,
    inspector: ContentInspector,
) -> EvidenceSnapshot:
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        row = await owned(session, workspace_id, actor, evidence_id)
        scanned = await inspection(session, row)
        if scanned is None:
            async with asyncio.timeout(30):
                data = await plaintext(session, row, wrapper)
                result = await inspector.inspect(data)
            validate_inspection(row, result)
            scanned = EvidenceInspection(
                evidence_id=row.id,
                workspace_id=row.workspace_id,
                verdict=result.verdict,
                engine=result.engine,
                definitions=result.definitions,
                inspected_at=result.inspected_at,
            )
            session.add(scanned)
        await authorize_actor(session, workspace_id, actor, "creator")
        session.add(observed(row, actor, request_id, "persona.evidence_inspected", scanned.verdict))
        response = snapshot(row, scanned.verdict)
    return response


async def read_evidence(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    evidence_id: UUID,
    wrapper: KeyWrapper,
) -> bytes:
    """Owner-only clean bytes, with a committed read event before releasing plaintext."""
    _, data = await read_document(session, workspace_id, actor, evidence_id, wrapper)
    return data


async def read_document(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    evidence_id: UUID,
    wrapper: KeyWrapper,
) -> tuple[EvidenceSnapshot, bytes]:
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        row = await owned(session, workspace_id, actor, evidence_id)
        scanned = await inspection(session, row)
        if snapshot(row, scanned.verdict if scanned else None).state != "clean":
            raise AccessDeniedError("private evidence is unavailable")
        async with asyncio.timeout(10):
            data = await plaintext(session, row, wrapper)
        if len(data) != row.byte_length or hashlib.sha256(data).hexdigest() != row.sha256:
            raise ValueError("private evidence integrity mismatch")
        await authorize_actor(session, workspace_id, actor, "creator")
        result = snapshot(row, "clean")
        if result.state != "clean":
            raise AccessDeniedError("private evidence expired during read")
        session.add(observed(row, actor, request_id, "persona.evidence_read", "clean"))
    return result, data


async def purge_expired(
    session: AsyncSession,
    workspace_id: UUID,
    actor: WorkflowActor,
    evidence_id: UUID,
    retention: RetentionGate,
) -> EvidenceSnapshot:
    """Explicit owner-scoped purge; scheduled retention worker is not activated."""
    request_id = uuid4()
    async with tracked_transaction(
        session, workspace_id, actor.actor_ref, request_id, actor_type=actor.audit_type
    ):
        row = await owned(session, workspace_id, actor, evidence_id)
        if datetime.now(UTC) < row.expires_at:
            raise ConflictError("evidence has not expired")
        async with asyncio.timeout(10):
            allowed = await retention.may_purge(workspace_id, evidence_id)
        if allowed is not True:
            raise AccessDeniedError("evidence retention decision denies deletion")
        stored = await payload(session, row)
        if stored is not None:
            await session.delete(stored)
            session.add(observed(row, actor, request_id, "persona.evidence_purged"))
        response = snapshot(row)
    return response
