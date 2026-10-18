"""Trusted fixture memberships; no application login or granting endpoint."""

from uuid import UUID, uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from accord.personas.contracts import PersonaDraft
from accord.personas.models import WorkspaceMember
from accord.personas.service import SaveCommand


@pytest_asyncio.fixture
async def workspace(session: AsyncSession) -> UUID:
    workspace_id = uuid4()
    session.add_all(
        [
            WorkspaceMember(workspace_id=workspace_id, actor_ref="creator-a", role="creator"),
            WorkspaceMember(workspace_id=workspace_id, actor_ref="creator-b", role="creator"),
            WorkspaceMember(workspace_id=workspace_id, actor_ref="viewer", role="viewer"),
        ]
    )
    await session.commit()
    return workspace_id


def command(name: str = "Fictional Nova", **changes: object) -> SaveCommand:
    content = PersonaDraft(
        name=name,
        biography="Fictional editorial character.",
        human_contribution="Original fictional character concept.",
        ai_disclosure="Synthetic fixture; no real person represented.",
    )
    return SaveCommand.model_validate({"request_id": uuid4(), "content": content, **changes})
