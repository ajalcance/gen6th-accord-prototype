"""Owner-terminal provisioning; no public enrollment or role-claim endpoint."""

import argparse
import asyncio
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from accord.auth.zynth_http import ZynthSettings
from accord.command.models import Event
from accord.db.connection import _get_sessionmaker
from accord.personas.identity_models import IdentityBinding
from accord.personas.models import WorkspaceMember


class ProvisionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    issuer: str
    tenant: UUID
    workspace: UUID
    subject: UUID
    role: Literal["creator", "reviewer", "viewer"]


async def provision(session: AsyncSession, command: ProvisionCommand) -> str:
    issuer = ZynthSettings(issuer=command.issuer, client_id="owner-provisioning").issuer
    async with session.begin():
        await session.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"),
            {"id": str(command.workspace)},
        )
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:id, 0))"),
            {"id": f"{issuer}:{command.tenant}:{command.subject}"},
        )
        row = await session.scalar(
            select(IdentityBinding).where(
                IdentityBinding.workspace_id == command.workspace,
                IdentityBinding.issuer == issuer,
                IdentityBinding.subject == command.subject,
            )
        )
        if row is not None:
            member = await session.get(WorkspaceMember, (command.workspace, row.actor_ref))
            if row.tenant_id != command.tenant or member is None or member.role != command.role:
                raise ValueError("existing binding differs; owner membership review required")
            return row.actor_ref
        actor = await new_binding(session, command, issuer)
    return actor


async def new_binding(session: AsyncSession, command: ProvisionCommand, issuer: str) -> str:
    actor = str(uuid4())
    session.add(WorkspaceMember(workspace_id=command.workspace, actor_ref=actor, role=command.role))
    await session.flush()
    session.add(
        IdentityBinding(
            workspace_id=command.workspace,
            issuer=issuer,
            subject=command.subject,
            tenant_id=command.tenant,
            actor_ref=actor,
        )
    )
    session.add(
        Event(
            event_id=uuid4().hex,
            ts=datetime.now(UTC),
            actor_type="system",
            actor_id="owner-terminal-bootstrap",
            tenant_id=command.workspace,
            category="workspace",
            action="workspace.membership_provisioned",
            outcome="success",
            severity="info",
            resource_type="workspace_member",
            resource_id=actor,
            source="server",
            metadata_={"role": command.role},
        )
    )
    await session.flush()
    return actor


async def run(command: ProvisionCommand) -> None:
    async with _get_sessionmaker()() as session:
        actor = await provision(session, command)
    print(f"accord_actor_id={actor}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("issuer", "tenant", "workspace", "subject", "role"):
        parser.add_argument(f"--{name}", required=True)
    command = ProvisionCommand.model_validate(vars(parser.parse_args()))
    asyncio.run(run(command))


if __name__ == "__main__":
    main()
