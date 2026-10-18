"""SQL transport denial and engine lifecycle evidence, without connecting to a database."""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool

from accord.config import DatabaseTransport, Environment, Settings
from accord.db import connection, runtime


def settings(
    url: str = "postgresql+asyncpg://accord_api:synthetic@127.0.0.1:5432/appdb",
) -> Settings:
    return Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        secret_key="synthetic-session-key",
        database_transport=DatabaseTransport.CLOUD_SQL_PROXY,
        database_url=url,
    )


@pytest.mark.parametrize("environment", [Environment.PRODUCTION, Environment.STAGING])
def test_missing_reviewed_transport_never_creates_an_engine(
    monkeypatch: pytest.MonkeyPatch, environment: Environment
) -> None:
    create = Mock()
    monkeypatch.setattr(runtime, "create_async_engine", create)
    value = settings().model_copy(
        update={"environment": environment, "database_transport": DatabaseTransport.LOCAL}
    )
    with pytest.raises(ValueError, match="reviewed Cloud SQL proxy transport required"):
        runtime.create_runtime_engine(value)
    create.assert_not_called()


@pytest.mark.parametrize(
    "url",
    [
        "malformed-private-credential",
        "postgresql+asyncpg://actor:synthetic@10.42.0.3:5432/appdb",
        "postgresql+asyncpg://actor:synthetic@localhost:5432/appdb",
        "postgresql+asyncpg://actor:synthetic@127.0.0.1:5433/appdb",
        "postgresql://actor:synthetic@127.0.0.1:5432/appdb",
        "postgresql+asyncpg://actor@127.0.0.1:5432/appdb",
        "postgresql+asyncpg://:synthetic@127.0.0.1:5432/appdb",
        "postgresql+asyncpg://actor:synthetic@127.0.0.1:5432/",
        "postgresql+asyncpg://actor:synthetic@127.0.0.1:5432/appdb?host=10.42.0.3",
        "postgresql+asyncpg://actor:synthetic@127.0.0.1:5432/appdb?ssl=disable",
        "postgresql+asyncpg://actor:synthetic@127.0.0.1:private-credential/appdb",
    ],
)
def test_invalid_proxy_url_denies_without_echoing_credentials(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    create = Mock()
    monkeypatch.setattr(runtime, "create_async_engine", create)
    with pytest.raises(ValueError, match="^valid loopback Cloud SQL proxy URL required$"):
        runtime.create_runtime_engine(settings(url))
    create.assert_not_called()


@pytest.mark.parametrize("login", sorted(runtime.ADMIN_LOGINS))
def test_administrative_login_is_only_available_to_the_migration_url_path(login: str) -> None:
    value = settings(f"postgresql+asyncpg://{login}:synthetic@127.0.0.1:5432/appdb")
    assert runtime.validated_database_url(value) == value.database_url
    with pytest.raises(ValueError, match="confined runtime SQL login required"):
        runtime.create_runtime_engine(value)


def test_real_disconnected_engine_has_bounded_pool_and_does_not_connect() -> None:
    engine = runtime.create_runtime_engine(settings())
    pool = engine.sync_engine.pool
    assert isinstance(pool, AsyncAdaptedQueuePool)
    assert pool.size() == 2
    assert pool.checkedout() == 0
    assert pool.timeout() == 5


def test_driver_connect_wait_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    create = Mock()
    monkeypatch.setattr(runtime, "create_async_engine", create)
    value = settings()
    runtime.create_runtime_engine(value)
    assert create.call_args.kwargs["connect_args"] == {"timeout": 5}
    assert create.call_args.kwargs["max_overflow"] == 0


def test_unrecognized_transport_cannot_fall_through_to_proxy_mode() -> None:
    value = settings().model_copy(update={"database_transport": "unreviewed"})
    with pytest.raises(ValueError, match="reviewed Cloud SQL proxy transport required"):
        runtime.create_runtime_engine(value)


def test_development_keeps_the_existing_local_url() -> None:
    value = Settings(_env_file=None, database_url="postgresql+asyncpg://local-db/disposable")
    assert runtime.validated_database_url(value) == value.database_url


def test_http_session_factory_uses_shared_engine_and_retains_commit_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = settings()
    engine = runtime.create_runtime_engine(value)
    create = Mock(return_value=engine)
    monkeypatch.setattr(connection, "get_settings", lambda: value)
    monkeypatch.setattr(connection, "create_runtime_engine", create)
    monkeypatch.setattr(connection, "_engine", None)
    monkeypatch.setattr(connection, "_sessionmaker", None)
    maker = connection._get_sessionmaker()
    assert connection._get_sessionmaker() is maker
    assert maker.kw["expire_on_commit"] is False
    create.assert_called_once_with(value)


@pytest.mark.parametrize("failure", [False, True])
async def test_compliance_pass_uses_shared_engine_and_disposes_after_failure(
    monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    from accord.command import worker

    value = settings()
    engine = AsyncMock()
    session = AsyncMock(spec=AsyncSession)
    context = AsyncMock()
    context.__aenter__.return_value = session
    create = Mock(return_value=engine)
    process = AsyncMock(side_effect=RuntimeError("synthetic outage") if failure else None)
    process.return_value = (1, 2, 3)
    monkeypatch.setattr(worker, "get_settings", lambda: value)
    monkeypatch.setattr(worker, "get_redis", Mock())
    monkeypatch.setattr(worker, "create_runtime_engine", create)
    monkeypatch.setattr(worker, "async_sessionmaker", Mock(return_value=Mock(return_value=context)))
    monkeypatch.setattr(worker, "process_once", process)
    if failure:
        with pytest.raises(RuntimeError, match="synthetic outage"):
            await worker.run_once()
    else:
        assert await worker.run_once() == (1, 2, 3)
    create.assert_called_once_with(value)
    engine.dispose.assert_awaited_once()
