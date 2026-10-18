"""Authorized immutable receipts; provider failures never become empty detections."""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.face_contracts import FaceCommand, FaceProfile, FaceResult, FaceSubject
from accord.personas.face_processing import detect_result, selected_result
from accord.personas.face_providers import FaceProviders
from accord.personas.face_repository import generation, reference
from accord.personas.face_storage import (
    analysis_pixels,
    command_fingerprint,
    load_result,
    store_result,
)
from accord.personas.photo_storage import photo_event
from accord.personas.repository import AccessDeniedError, ConflictError, authorize
from accord.personas.transactions import tracked_transaction


async def profile(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    subject: FaceSubject,
    wrapper: KeyWrapper | None,
    providers: FaceProviders | None,
) -> FaceProfile:
    request = uuid4()
    async with tracked_transaction(session, workspace, actor, request):
        await authorize(session, workspace, actor, write=False)
        await reference(session, workspace, actor, subject, write=False)
        row = await generation(session, workspace, subject)
        if row is not None and wrapper is None:
            raise RuntimeError("face key service unavailable")
        latest = (
            await load_result(row, wrapper) if row is not None and wrapper is not None else None
        )
        result = FaceProfile(
            workspace_id=workspace,
            **subject.model_dump(),
            latest=latest,
            provider_ready=providers is not None and wrapper is not None,
        )
        session.add(
            photo_event("persona.portrait_read", workspace, actor, subject.portrait_id, request)
        )
    return result


async def process(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    command: FaceCommand,
    wrapper: KeyWrapper | None,
    providers: FaceProviders | None,
) -> FaceResult:
    async with tracked_transaction(session, workspace, actor, command.request_id):
        return await process_in_transaction(session, workspace, actor, command, wrapper, providers)


async def process_in_transaction(
    session: AsyncSession,
    workspace: UUID,
    actor: str,
    command: FaceCommand,
    wrapper: KeyWrapper | None,
    providers: FaceProviders | None,
) -> FaceResult:
    await authorize(session, workspace, actor, write=True)
    photo, capture = await reference(session, workspace, actor, command, write=True)
    if wrapper is None:
        raise RuntimeError("face key service unavailable")
    prior = await generation(session, workspace, command, request=command.request_id)
    if prior is not None:
        if prior.actor_ref != actor or prior.fingerprint != command_fingerprint(command):
            raise ConflictError("face request reused with different intent")
        result = await load_result(prior, wrapper)
    else:
        if providers is None:
            raise RuntimeError("face processing provider unavailable")
        parent = await selected_parent(session, workspace, command, capture.sha256, wrapper)
        pixels = await analysis_pixels(photo, capture, wrapper)
        result, vectors = await run_processing(
            workspace,
            command,
            pixels,
            capture.sha256,
            capture.width,
            capture.height,
            parent,
            providers,
        )
        await store_result(session, result, command, actor, vectors, wrapper)
        event = photo_event(
            "persona.portrait_inspected", workspace, actor, photo.id, command.request_id
        )
        event.metadata_ = {
            "operation": "face_representation" if parent else "face_detection",
            "state": result.state,
        }
        session.add(event)
    await authorize(session, workspace, actor, write=True)
    await reference(session, workspace, actor, command, write=True)
    return result


async def selected_parent(
    session: AsyncSession,
    workspace: UUID,
    command: FaceCommand,
    digest: str,
    wrapper: KeyWrapper,
) -> FaceResult | None:
    if command.generation_id is None:
        return None
    row = await generation(session, workspace, command, identity=command.generation_id)
    if row is None:
        raise AccessDeniedError("face generation access denied")
    parent = await load_result(row, wrapper)
    if parent.source_sha256 != digest:
        raise ConflictError("face generation capture changed")
    return parent


async def run_processing(
    workspace: UUID,
    command: FaceCommand,
    pixels: bytes,
    digest: str,
    width: int,
    height: int,
    parent: FaceResult | None,
    providers: FaceProviders,
) -> tuple[FaceResult, tuple[tuple[float, ...], ...]]:
    try:
        async with asyncio.timeout(55):
            if parent is not None:
                return await selected_result(command, parent, pixels, providers)
            return (
                await detect_result(workspace, command, pixels, digest, width, height, providers),
                (),
            )
    except Exception as exc:
        raise RuntimeError("face processing unavailable") from exc
