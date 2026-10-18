"""Owner/CI PostgreSQL proof of atomic capture and immutable approved reference history."""

from datetime import datetime, tzinfo
from typing import Self
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.capture_contracts import CaptureQuery, ReferenceChange
from accord.personas.capture_models import PortraitCapture, VersionReference
from accord.personas.capture_reads import capture_profile
from accord.personas.contracts import PersonaVersion
from accord.personas.models import Version
from accord.personas.photo_contracts import PhotoChange
from accord.personas.photo_models import Portrait, PortraitPayload
from accord.personas.photo_reads import reference_thumbnail
from accord.personas.portrait_search import search_portraits
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import save
from accord.personas.workflow_contracts import WorkflowActor
from personas.conftest import command
from personas.test_photo_storage import FixtureWrapper, body, staged


async def register(session: AsyncSession, workspace: UUID, portrait: UUID) -> PersonaVersion:
    return await save(
        session,
        workspace,
        "creator-a",
        command(photo=PhotoChange(action="attach", upload_id=portrait)),
    )


@pytest.mark.asyncio
async def test_approval_reorder_clear_and_replay_preserve_earlier_versions(
    session: AsyncSession, workspace: UUID
) -> None:
    wrapper = FixtureWrapper()
    _, first = await staged(session, workspace, wrapper)
    _, second = await staged(session, workspace, wrapper)
    initial = await register(session, workspace, first)
    profile = await capture_profile(
        session, workspace, "viewer", CaptureQuery(version_id=initial.version_id)
    )
    assert [item.portrait_id for item in profile.references] == [first]
    assert profile.capture and profile.capture.source_width == 32
    intent = command(
        persona_id=initial.persona_id,
        expected_revision=1,
        references=ReferenceChange(action="replace", upload_ids=(second, first)),
    )
    next_version = await save(session, workspace, "creator-a", intent)
    assert await save(session, workspace, "creator-a", intent) == next_version
    next_profile = await capture_profile(
        session, workspace, "viewer", CaptureQuery(version_id=next_version.version_id)
    )
    assert [item.portrait_id for item in next_profile.references] == [second, first]
    assert await reference_thumbnail(
        session, workspace, "viewer", next_version.version_id, second, wrapper
    )
    cleared = await save(
        session,
        workspace,
        "creator-a",
        command(
            persona_id=initial.persona_id,
            expected_revision=2,
            references=ReferenceChange(action="replace"),
        ),
    )
    assert not (
        await capture_profile(
            session, workspace, "viewer", CaptureQuery(version_id=cleared.version_id)
        )
    ).references
    historical = await capture_profile(
        session, workspace, "viewer", CaptureQuery(version_id=initial.version_id)
    )
    assert historical.references[0].portrait_id == first
    with pytest.raises(AccessDeniedError):
        await reference_thumbnail(session, workspace, "viewer", initial.version_id, second, wrapper)


@pytest.mark.asyncio
async def test_reference_ownership_denial_is_atomic_and_upload_metadata_is_owner_only(
    session: AsyncSession, workspace: UUID
) -> None:
    _, other = await staged(session, workspace, FixtureWrapper(), "creator-b")
    with pytest.raises(AccessDeniedError):
        await capture_profile(session, workspace, "viewer", CaptureQuery(upload_id=other))
    with pytest.raises(AccessDeniedError):
        await save(
            session,
            workspace,
            "creator-a",
            command(references=ReferenceChange(action="replace", upload_ids=(other,))),
        )
    assert await session.scalar(select(func.count()).select_from(Version)) == 0
    assert await session.scalar(select(func.count()).select_from(VersionReference)) == 0
    await session.rollback()
    with pytest.raises(AccessDeniedError):
        await capture_profile(session, uuid4(), "creator-b", CaptureQuery(upload_id=other))


@pytest.mark.asyncio
async def test_analysis_wrapping_failure_rolls_back_original_and_thumbnail(
    session: AsyncSession, workspace: UUID
) -> None:
    class ThirdFailure(FixtureWrapper):
        async def wrap(self, key: bytes, context: bytes) -> tuple[str, bytes]:
            if len(self.keys) == 2:
                raise RuntimeError("synthetic analysis key outage")
            return await super().wrap(key, context)

    with pytest.raises(RuntimeError, match="analysis key outage"):
        await staged(session, workspace, ThirdFailure())
    for table in (Portrait, PortraitPayload, PortraitCapture):
        assert await session.scalar(select(func.count()).select_from(table)) == 0


@pytest.mark.asyncio
async def test_expired_approved_reference_is_kept_but_new_expired_stage_is_rejected(
    session: AsyncSession, workspace: UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    wrapper = FixtureWrapper()
    _, first = await staged(session, workspace, wrapper)
    _, unused = await staged(session, workspace, wrapper)
    initial = await save(
        session,
        workspace,
        "creator-a",
        command(photo=PhotoChange(action="attach", upload_id=first)),
    )

    class Future(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            return cls.fromtimestamp(datetime.now(tz).timestamp() + 172800, tz)

    monkeypatch.setattr("accord.personas.reference_binding.datetime", Future)
    kept = await save(
        session, workspace, "creator-a", command(persona_id=initial.persona_id, expected_revision=1)
    )
    assert (
        await capture_profile(
            session, workspace, "viewer", CaptureQuery(version_id=kept.version_id)
        )
    ).references[0].portrait_id == first
    with pytest.raises(ConflictError):
        await save(
            session,
            workspace,
            "creator-a",
            command(
                persona_id=initial.persona_id,
                expected_revision=2,
                references=ReferenceChange(action="replace", upload_ids=(unused,)),
            ),
        )


@pytest.mark.asyncio
async def test_exact_search_finds_explicit_secondary_reference_without_enrolling_query(
    session: AsyncSession, workspace: UUID
) -> None:
    value, secondary = await staged(session, workspace, FixtureWrapper())
    version = await save(
        session,
        workspace,
        "creator-a",
        command(references=ReferenceChange(action="replace", upload_ids=(secondary,))),
    )
    found = await search_portraits(
        session, workspace, WorkflowActor(actor_ref="viewer", kind="human"), body(value)
    )
    assert found.items[0].version_id == version.version_id
    assert await session.scalar(select(func.count()).select_from(Portrait)) == 1


@pytest.mark.asyncio
async def test_capture_ciphertext_is_not_exposed_by_profile(
    session: AsyncSession, workspace: UUID
) -> None:
    _, portrait = await staged(session, workspace, FixtureWrapper())
    profile = await capture_profile(
        session, workspace, "creator-a", CaptureQuery(upload_id=portrait)
    )
    assert profile.capture and profile.recognition == "not_processed" and not profile.references
    row = await session.get(PortraitCapture, portrait)
    assert row and not row.ciphertext.startswith(b"\x89PNG")
    public = profile.model_dump_json()
    assert all(field not in public for field in ("ciphertext", "wrapped_key", "nonce", "key_id"))
