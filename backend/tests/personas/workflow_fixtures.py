"""Explicit trusted human fixtures; no identity or membership granting endpoint."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.contracts import PersonaVersion
from accord.personas.models import WorkspaceMember
from accord.personas.service import save
from accord.personas.workflow_contracts import ReviewCommand, WorkflowActor
from personas.conftest import command


def human(actor_ref: str) -> WorkflowActor:
    return WorkflowActor(actor_ref=actor_ref, kind="human")


async def draft_for_review(session: AsyncSession, workspace: UUID) -> PersonaVersion:
    session.add_all(
        [
            WorkspaceMember(workspace_id=workspace, actor_ref="reviewer-a", role="reviewer"),
            WorkspaceMember(workspace_id=workspace, actor_ref="reviewer-b", role="reviewer"),
        ]
    )
    await session.commit()
    return await save(session, workspace, "creator-a", command())


def review_intent(target_version_id: UUID, **changes: object) -> ReviewCommand:
    return ReviewCommand.model_validate(
        {
            "request_id": uuid4(),
            "version_id": target_version_id,
            "decision": "approved",
            "statement": "Fictional evidence reviewed; no legal determination.",
            **changes,
        }
    )
