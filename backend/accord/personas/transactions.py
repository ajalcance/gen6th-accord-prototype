"""Own the mutation transaction and record authorization/conflict rejections."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from accord.command.models import Event
from accord.logger import logger
from accord.personas.repository import AccessDeniedError, ConflictError


@asynccontextmanager
async def tracked_transaction(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    request_id: UUID,
    *,
    actor_type: Literal["user", "agent", "system"] = "user",
) -> AsyncIterator[None]:
    """Rollback failed work before independently recording its bounded rejection."""
    try:
        async with session.begin():
            yield
    except (AccessDeniedError, ConflictError) as exc:
        try:
            await record_rejection(session, workspace_id, actor_ref, request_id, exc, actor_type)
        except (DBAPIError, RuntimeError):
            logger.error("persona rejection recording failed (request_id=%s)", request_id)
            raise
        raise
    except (DBAPIError, RuntimeError):
        logger.error("persona transaction failed (request_id=%s)", request_id)
        raise


async def record_rejection(
    session: AsyncSession,
    workspace_id: UUID,
    actor_ref: str,
    request_id: UUID,
    error: AccessDeniedError | ConflictError,
    actor_type: Literal["user", "agent", "system"] = "user",
) -> None:
    denied = isinstance(error, AccessDeniedError)
    async with session.begin():
        session.add(
            Event(
                event_id=uuid4().hex,
                ts=datetime.now(UTC),
                actor_type=actor_type if actor_ref else "system",
                actor_id=actor_ref or None,
                tenant_id=workspace_id,
                category="persona",
                action="persona.access_denied" if denied else "persona.write_conflict",
                outcome="denied" if denied else "failure",
                severity="warn",
                source="server",
                correlation_id=str(request_id),
                metadata_={},
            )
        )
