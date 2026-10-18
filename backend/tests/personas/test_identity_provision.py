"""Owner/CI SQL proof: canonical provisioning, atomic observations and no implicit grants."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.personas.identity_models import IdentityBinding
from accord.personas.identity_repository import resolve_identity
from accord.personas.models import WorkspaceMember
from accord.personas.provision import ProvisionCommand, provision


async def test_provisioning_is_atomic_canonical_and_idempotent(session: AsyncSession) -> None:
    command = ProvisionCommand(
        issuer="https://identity.example.invalid",
        tenant=uuid4(),
        workspace=uuid4(),
        subject=uuid4(),
        role="creator",
    )
    actor = await provision(session, command)
    assert str(UUID(actor)) == actor and actor != str(command.subject)
    assert await provision(session, command) == actor
    member = await session.get(WorkspaceMember, (command.workspace, actor))
    assert member is not None and member.role == "creator"
    events = list(
        await session.scalars(
            select(Event).where(Event.action == "workspace.membership_provisioned")
        )
    )
    assert len(events) == 1 and events[0].source == "server"
    assert events[0].actor_id == "owner-terminal-bootstrap" and events[0].metadata_ == {
        "role": "creator"
    }
    assert await session.scalar(select(func.count()).select_from(IdentityBinding)) == 1


async def test_provisioning_never_silently_changes_existing_role(session: AsyncSession) -> None:
    command = ProvisionCommand(
        issuer="https://identity.example.invalid",
        tenant=uuid4(),
        workspace=uuid4(),
        subject=uuid4(),
        role="viewer",
    )
    await provision(session, command)
    with pytest.raises(ValueError, match="review required"):
        await provision(session, command.model_copy(update={"role": "creator"}))
    member = await session.scalar(select(WorkspaceMember))
    assert member is not None and member.role == "viewer"


async def test_resolver_reads_only_exact_existing_binding(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import MagicMock

    import accord.personas.identity_repository as repository

    command = ProvisionCommand(
        issuer="https://identity.example.invalid",
        tenant=uuid4(),
        workspace=uuid4(),
        subject=uuid4(),
        role="reviewer",
    )
    actor = await provision(session, command)
    await session.close()
    monkeypatch.setattr(repository, "_get_sessionmaker", MagicMock(return_value=lambda: session))
    assert (
        await resolve_identity(command.issuer, command.tenant, command.subject, command.workspace)
        == actor
    )
    assert (
        await resolve_identity(command.issuer, uuid4(), command.subject, command.workspace) is None
    )
    assert await resolve_identity(command.issuer, command.tenant, command.subject, uuid4()) is None
