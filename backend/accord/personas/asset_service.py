"""Enroll exact inspected bytes under an explicit creator statement; no rights inference."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.asset_contracts import EnrollAsset, EnrolledAsset
from accord.personas.asset_models import AssetEnrollment
from accord.personas.campaign_contracts import AssetSnapshot
from accord.personas.campaign_models import PersonaAsset
from accord.personas.evidence_models import PrivateEvidence
from accord.personas.evidence_repository import inspection, owned, payload, snapshot
from accord.personas.repository import AccessDeniedError, ConflictError
from accord.personas.service import fingerprint
from accord.personas.transactions import tracked_transaction
from accord.personas.workflow_contracts import WorkflowActor
from accord.personas.workflow_events import decision_event
from accord.personas.workflow_repository import authorize_actor, locked_version, require_current


async def enroll(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: EnrollAsset
) -> EnrolledAsset:
    async with tracked_transaction(
        session, workspace, actor.actor_ref, command.request_id, actor_type=actor.audit_type
    ):
        await authorize_actor(session, workspace, actor, "creator")
        version, persona = await locked_version(session, workspace, command.version_id)
        if persona.owner_ref != actor.actor_ref:
            raise AccessDeniedError("asset enrollment requires the owner")
        existing = await session.scalar(
            select(AssetEnrollment).where(
                AssetEnrollment.workspace_id == workspace,
                AssetEnrollment.owner_ref == actor.actor_ref,
                AssetEnrollment.request_id == command.request_id,
            )
        )
        if existing is not None:
            if existing.fingerprint != fingerprint(command):
                raise ConflictError("asset enrollment intent changed")
            asset = await session.get(PersonaAsset, existing.asset_id)
            if asset is None:
                raise RuntimeError("enrollment asset missing")
        else:
            require_current(version, persona)
            asset = await new_asset(session, workspace, actor, command)
        await authorize_actor(session, workspace, actor, "creator")
        result = EnrolledAsset(
            workspace_id=workspace,
            version_id=version.id,
            evidence_id=command.evidence_id,
            asset=AssetSnapshot(id=asset.id, digest=asset.digest, label=asset.label),
        )
    return result


async def enrollment_evidence(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: EnrollAsset
) -> PrivateEvidence:
    evidence = await owned(session, workspace, actor, command.evidence_id)
    scanned = await inspection(session, evidence)
    if (
        evidence.version_id != command.version_id
        or scanned is None
        or snapshot(evidence, scanned.verdict).state != "clean"
        or await payload(session, evidence) is None
    ):
        raise AccessDeniedError("enrollment requires current clean exact-version evidence")
    duplicate = await session.scalar(
        select(AssetEnrollment.asset_id).where(
            AssetEnrollment.workspace_id == workspace,
            AssetEnrollment.version_id == command.version_id,
            AssetEnrollment.evidence_id == evidence.id,
        )
    )
    if duplicate is not None:
        raise ConflictError("these bytes are already enrolled for this version")
    count = await session.scalar(
        select(func.count())
        .select_from(PersonaAsset)
        .where(
            PersonaAsset.workspace_id == workspace, PersonaAsset.version_id == command.version_id
        )
    )
    if count is None or count >= 20:
        raise ConflictError("version asset limit reached")
    return evidence


async def new_asset(
    session: AsyncSession, workspace: UUID, actor: WorkflowActor, command: EnrollAsset
) -> PersonaAsset:
    evidence = await enrollment_evidence(session, workspace, actor, command)
    asset = PersonaAsset(
        id=uuid4(),
        workspace_id=workspace,
        version_id=command.version_id,
        digest=evidence.sha256,
        label=command.label,
    )
    session.add(asset)
    await session.flush()
    session.add(
        AssetEnrollment(
            asset_id=asset.id,
            workspace_id=workspace,
            version_id=command.version_id,
            evidence_id=evidence.id,
            owner_ref=actor.actor_ref,
            request_id=command.request_id,
            fingerprint=fingerprint(command),
            permission_statement=command.permission_statement,
            recorded_at=datetime.now(UTC),
        )
    )
    session.add(
        decision_event(
            workspace_id=workspace,
            actor_ref=actor.actor_ref,
            request_id=command.request_id,
            record_id=asset.id,
            version_id=command.version_id,
            event_id=uuid4().hex,
            recorded_at=datetime.now(UTC),
            action="persona.asset_registered",
        )
    )
    return asset
