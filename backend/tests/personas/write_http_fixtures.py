"""Test-only mutable synthetic identity and actual PostgreSQL service routing."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import UUID

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from accord.db.connection import get_db
from accord.personas.campaign_models import CampaignDecision, CampaignOffer
from accord.personas.models import Version
from accord.personas.review_models import ReviewRecord
from accord.personas.write_http import create_write_router
from personas.test_session_boundary import verified


@asynccontextmanager
async def write_client(session: AsyncSession) -> AsyncIterator[tuple[AsyncClient, AsyncMock]]:
    provider = AsyncMock()
    provider.verify.return_value = verified(actor_ref="creator-a")
    app = FastAPI()
    app.include_router(create_write_router(provider))

    async def database() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, provider


async def row_counts(session: AsyncSession, workspace: UUID) -> tuple[int, ...]:
    async with session.begin():
        counts = [
            int(
                await session.scalar(
                    select(func.count()).select_from(model).where(model.workspace_id == workspace)
                )
                or 0
            )
            for model in (Version, ReviewRecord, CampaignOffer, CampaignDecision)
        ]
    return tuple(counts)
