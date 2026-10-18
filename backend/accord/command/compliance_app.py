"""Health-only continuous worker lifecycle using unchanged compliance processing."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from accord.cache.redis import get_redis
from accord.command.compliance_config import validate_compliance
from accord.command.compliance_supervisor import ComplianceSupervisor
from accord.command.worker import run_once
from accord.config import get_settings
from accord.db import connection
from accord.logger import setup_logging
from accord.personas.runtime_role import verify_runtime_role

STARTUP_SECONDS = 45
ROLE_SECONDS = 10
CLOSE_SECONDS = 2


async def close_redis(redis: Redis) -> None:
    try:
        async with asyncio.timeout(CLOSE_SECONDS):
            await redis.aclose()
    except Exception:
        raise RuntimeError("compliance Redis cleanup unavailable") from None


async def verify_compliance_role() -> None:
    """Reuse the existing effective-role predicate and close its idle startup pool."""
    try:
        async with asyncio.timeout(ROLE_SECONDS):
            await verify_runtime_role()
    finally:
        if connection._engine is not None:
            async with asyncio.timeout(CLOSE_SECONDS):
                await connection._engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(get_settings().log_level)
    worker: ComplianceSupervisor = app.state.compliance
    redis = None
    try:
        async with asyncio.timeout(STARTUP_SECONDS):
            await verify_compliance_role()
            redis = get_redis()
            await worker.cycle()
            worker.start()
        yield
    except Exception:
        raise RuntimeError("compliance startup or lifecycle unavailable") from None
    finally:
        try:
            await worker.stop()
        finally:
            if redis is not None:
                await close_redis(redis)


def create_compliance_app() -> FastAPI:
    settings = get_settings()
    validate_compliance(settings)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    worker = ComplianceSupervisor(run_once, settings.command_poll_seconds)
    app.state.compliance = worker

    @app.get("/health")
    async def health() -> JSONResponse:
        state = worker.health()
        return JSONResponse(
            {"status": state, "scope": "worker_pass_progress"},
            status_code=200 if state == "progressing" else 503,
            headers={"Cache-Control": "no-store"},
        )

    return app
