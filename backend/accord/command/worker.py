"""Background worker: ingest, seal, evaluate durable persona events, then expire history.

Run it as its own process:  ``python -m accord.command.worker``

Fail-open by design: if it dies, requests are unaffected — only ingest/sealing pauses.
"""

from __future__ import annotations

import asyncio

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from accord.cache.redis import get_redis
from accord.command.audit import seal_new
from accord.command.consumer import consume_once, purge_expired
from accord.command.detection import evaluate_once
from accord.config import get_settings
from accord.db.runtime import create_runtime_engine
from accord.logger import logger, setup_logging


async def process_once(redis: Redis, session: AsyncSession) -> tuple[int, int, int]:
    """Redis outage pauses ingestion, not sealing of already durable events."""
    try:
        stored = await consume_once(redis, session)
    except RedisError:
        await session.rollback()
        logger.warning("worker ingestion unavailable; processing durable PostgreSQL events")
        stored = 0
    sealed = await seal_new(session)
    evaluated = await evaluate_once(session)
    if evaluated:
        logger.info("worker: %d persona events evaluated", evaluated)
    purged = await purge_expired(session)
    return stored, sealed, purged


async def run_once() -> tuple[int, int, int]:
    """Ingest, seal, evaluate and expire; return ingestion/sealing/expiry counts."""
    redis = get_redis()
    engine = create_runtime_engine(get_settings())
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            return await process_once(redis, session)
    finally:
        await engine.dispose()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("command-worker started (poll=%ss)", settings.command_poll_seconds)
    while True:
        try:
            stored, sealed, _purged = await run_once()
            if stored or sealed:
                logger.info("worker: %d ingested, %d sealed", stored, sealed)
        except Exception as exc:  # noqa: BLE001 — the loop must survive transient errors
            logger.error("worker pass failed (%s)", type(exc).__name__)
        await asyncio.sleep(settings.command_poll_seconds)


if __name__ == "__main__":
    asyncio.run(main())
