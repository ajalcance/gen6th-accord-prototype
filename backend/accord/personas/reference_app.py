"""Reference-only ASGI factory; existing verified task routes, no browser surface."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from accord import __version__
from accord.config import get_settings
from accord.logger import setup_logging
from accord.personas.job_http import create_task_router
from accord.personas.reference_bootstrap import build_reference
from accord.personas.runtime_role import verify_runtime_role


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Verify the actual SQL role before serving; lazy adapters own no open clients."""
    setup_logging(get_settings().log_level)
    await verify_runtime_role()
    yield


def create_reference_app() -> FastAPI:
    """Only process health and existing machine-authenticated execute/reconcile routes."""
    runtime = build_reference(get_settings())
    app = FastAPI(
        title="Gen6th Accord reference worker",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(create_task_router(runtime.jobs, runtime.identity))
    return app
