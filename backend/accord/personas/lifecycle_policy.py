"""Live permission policy; no browser claims or offline signatures grant current use."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from accord.config import get_settings
from accord.personas.lifecycle_contracts import Assessment, Dossier
from accord.personas.lifecycle_models import LifecycleRecord
from accord.personas.lifecycle_reads import requirements
from accord.personas.lifecycle_repository import is_suspended, latest
from accord.personas.models import WorkspaceMember
from accord.personas.production_contracts import ProductionUse


async def lifecycle_blocks(
    session: AsyncSession,
    workspace: UUID,
    persona: UUID,
    version: UUID,
    production: ProductionUse | None,
    starts_at: datetime,
    ends_at: datetime,
) -> list[str]:
    bound = production is not None and production.governance_profile_id is not None
    if not get_settings().persona_lifecycle_enabled:
        return ["lifecycle_unavailable"] if bound else []
    reasons: list[str] = []
    if await is_suspended(session, workspace, persona):
        reasons.append("performer_suspended")
    profile = await latest(session, workspace, persona, "dossier", version)
    if profile is None:
        return reasons + ["governance_missing"]
    dossier = Dossier.model_validate(profile.content)
    if (
        production is None
        or production.governance_profile_id != profile.id
        or production.responsible_operator != dossier.operator.actor_ref
    ):
        reasons.append("governance_changed")
    member = await session.get(
        WorkspaceMember, (workspace, dossier.operator.actor_ref), populate_existing=True
    )
    if member is None:
        reasons.append("operator_unavailable")
    reasons.extend(await assessment_blocks(session, workspace, persona, profile, ends_at))
    reasons.extend(rights_blocks(dossier, production, starts_at, ends_at))
    return reasons


async def assessment_blocks(
    session: AsyncSession,
    workspace: UUID,
    persona: UUID,
    profile: LifecycleRecord,
    ends_at: datetime,
) -> list[str]:
    assessments = await requirements(session, workspace, persona, profile)
    if any(item.status != "approved" for item in assessments):
        return ["governance_review_required"]
    elif any(
        item.assessment is None
        or not isinstance(item.assessment.content, Assessment)
        or item.assessment.content.valid_until < ends_at
        for item in assessments
    ):
        return ["governance_expired"]
    return []


def rights_blocks(
    dossier: Dossier,
    production: ProductionUse | None,
    starts_at: datetime,
    ends_at: datetime,
) -> list[str]:
    reasons: list[str] = []
    now = datetime.now(UTC)
    if any(
        right.starts_at > starts_at or right.ends_at < ends_at or right.ends_at <= now
        for right in dossier.rights
    ):
        reasons.append("rights_window_unavailable")
    if (
        production
        and production.voice_use
        and not any(right.kind == "voice" for right in dossier.rights)
    ):
        reasons.append("voice_rights_missing")
    return reasons
