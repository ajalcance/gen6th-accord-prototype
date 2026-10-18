"""Reviewed SQL transport and bounded runtime engines; no connector or credential discovery."""

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from accord.config import DatabaseTransport, Environment, Settings

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 5432
POOL_SIZE = 2
POOL_WAIT_SECONDS = 5
CONNECT_WAIT_SECONDS = 5
ADMIN_LOGINS = frozenset({"postgres", "accord_migrator", "cloudsqladmin", "cloudsqlsuperuser"})


def validated_database_url(settings: Settings, *, runtime: bool = False) -> str:
    """Fail closed on an unreviewed remote transport, without printing URL credentials."""
    if settings.database_transport is DatabaseTransport.LOCAL:
        if settings.environment is not Environment.DEVELOPMENT:
            raise ValueError("reviewed Cloud SQL proxy transport required")
        return settings.database_url
    if settings.database_transport is not DatabaseTransport.CLOUD_SQL_PROXY:
        raise ValueError("reviewed Cloud SQL proxy transport required")
    try:
        address = make_url(settings.database_url)
        valid = (
            address.drivername == "postgresql+asyncpg"
            and address.host == PROXY_HOST
            and address.port == PROXY_PORT
            and bool(address.database)
            and bool(address.username)
            and bool(address.password)
            and not address.query
        )
    except (ArgumentError, ValueError):
        raise ValueError("valid loopback Cloud SQL proxy URL required") from None
    if not valid:
        raise ValueError("valid loopback Cloud SQL proxy URL required")
    if runtime and address.username and address.username.casefold() in ADMIN_LOGINS:
        raise ValueError("confined runtime SQL login required")
    return settings.database_url


def create_runtime_engine(settings: Settings) -> AsyncEngine:
    """Apply the same capacity and connection bounds to HTTP and compliance engines."""
    return create_async_engine(
        validated_database_url(settings, runtime=True),
        pool_pre_ping=True,
        pool_size=POOL_SIZE,
        max_overflow=0,
        pool_timeout=POOL_WAIT_SECONDS,
        connect_args={"timeout": CONNECT_WAIT_SECONDS},
    )
