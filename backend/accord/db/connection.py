"""Async database engine, session factory, and the FastAPI ``get_db`` dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from accord.config import get_settings
from accord.db.runtime import create_runtime_engine, validated_database_url


def get_database_url() -> str:
    """The async SQLAlchemy database URL."""
    return validated_database_url(get_settings())


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _engine, _sessionmaker
    if _sessionmaker is None:
        _engine = create_runtime_engine(get_settings())
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _sessionmaker


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a database session scoped to the request."""
    async with _get_sessionmaker()() as session:
        yield session
