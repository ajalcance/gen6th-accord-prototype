"""Connection timeout and disposal on the real Alembic environment's failure paths."""

import runpy
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from alembic import context
from alembic.config import Config
from sqlalchemy import pool


@pytest.mark.parametrize("failure", [None, "connect", "migration"])
async def test_migration_environment_keeps_null_pool_and_disposes_every_outcome(
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    url = "postgresql+asyncpg://synthetic:synthetic@127.0.0.1:5432/disposable"
    config = Config()
    config.set_main_option("sqlalchemy.url", url)
    connection = AsyncMock()
    manager = AsyncMock()
    manager.__aenter__.return_value = connection
    engine = AsyncMock()
    engine.connect = Mock(return_value=manager)
    if failure == "connect":
        manager.__aenter__.side_effect = RuntimeError("synthetic connection failure")
    if failure == "migration":
        connection.run_sync.side_effect = RuntimeError("synthetic migration failure")
    create = Mock(return_value=engine)
    monkeypatch.setattr("sqlalchemy.ext.asyncio.create_async_engine", create)
    monkeypatch.setattr(context, "config", config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", Mock(return_value=True))
    monkeypatch.setattr(context, "configure", Mock())
    monkeypatch.setattr(context, "begin_transaction", Mock(return_value=nullcontext()))
    monkeypatch.setattr(context, "run_migrations", Mock())
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "migrations/env.py"))
    if failure:
        with pytest.raises(
            RuntimeError,
            match=f"synthetic {failure if failure != 'connect' else 'connection'} failure",
        ):
            await namespace["run_async_migrations"]()
    else:
        await namespace["run_async_migrations"]()
    create.assert_called_once_with(url, poolclass=pool.NullPool, connect_args={"timeout": 5})
    engine.dispose.assert_awaited_once()
