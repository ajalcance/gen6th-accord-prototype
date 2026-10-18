"""Real pool saturation/recovery on the existing disposable SQL fixture only."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from sqlalchemy.ext.asyncio import AsyncEngine

from accord.config import Settings
from accord.db.runtime import create_runtime_engine


async def test_third_checkout_is_bounded_and_release_restores_capacity(
    db_engine: AsyncEngine,
) -> None:
    value = Settings(
        _env_file=None,
        database_url=db_engine.url.render_as_string(hide_password=False),
    )
    engine = create_runtime_engine(value)
    try:
        async with engine.connect() as first, engine.connect() as second:
            assert await first.scalar(text("SELECT 1")) == 1
            assert await second.scalar(text("SELECT 1")) == 1
            with pytest.raises(PoolTimeoutError, match="QueuePool limit of size 2 overflow 0"):
                async with engine.connect():
                    pytest.fail("third connection must not exceed the pool bound")
        async with engine.connect() as recovered:
            assert await recovered.scalar(text("SELECT 1")) == 1
    finally:
        await engine.dispose()
