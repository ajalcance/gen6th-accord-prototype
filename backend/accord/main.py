"""Gen6th Accord backend.

FastAPI application entrypoint. Minimal foundation: system endpoints only. Feature
routers are mounted here as they are built (one module per PR), keeping this file thin.

The project name is kept on its own short summary line: appending to it would push the
line past the 100-char ruff/black limit for a long name and fail a fresh `make check`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from accord import __version__
from accord.api import routes_client_events
from accord.auth.browser_routes import router as auth_router
from accord.auth.zynth_bootstrap import build_zynth_verifier
from accord.config import get_settings
from accord.logger import logger, setup_logging
from accord.personas.asset_http import create_asset_router
from accord.personas.assistant_google import build_provider
from accord.personas.assistant_http import create_assistant_router
from accord.personas.credit_http import create_credit_router
from accord.personas.evidence_http import create_evidence_router
from accord.personas.evidence_inspector import DocumentInspector
from accord.personas.governance_http import create_governance_read_router
from accord.personas.job_http import create_job_router, create_task_router
from accord.personas.lifecycle_http import create_lifecycle_router
from accord.personas.passport_http import create_passport_router
from accord.personas.photo_bootstrap import photo_providers
from accord.personas.photo_http import create_photo_router
from accord.personas.photo_inspector import PillowClamdInspector
from accord.personas.publication_http import (
    create_public_passport_router,
    create_publication_router,
)
from accord.personas.read_http import create_read_router
from accord.personas.runtime_bootstrap import build_runtime
from accord.personas.runtime_http import create_runtime_router
from accord.personas.runtime_role import verify_runtime_role
from accord.personas.runtime_startup import prepare_inspection
from accord.personas.write_http import create_write_router

# Held as a constant, not interpolated into each call site: a long project slug would push
# a log line past the 100-char ruff/black limit and make a freshly generated repo fail
# `make check`. Only this one short line varies with the slug.
SERVICE_NAME = "gen6th-accord"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle."""
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        if settings.persona_api_enabled:
            await verify_runtime_role()
        await prepare_inspection(settings)
        logger.info(
            "%s starting (env=%s, version=%s)",
            SERVICE_NAME,
            settings.environment.value,
            __version__,
        )
        yield
    finally:
        await _app.state.persona_runtime.close()
        logger.info("%s shutting down", SERVICE_NAME)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Gen6th Accord",
        version=__version__,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Process health after ASGI startup; no ongoing dependency-health assertion."""
        return {"status": "ok", "version": __version__}

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        """Service banner."""
        return {"service": SERVICE_NAME, "version": __version__}

    verifier = build_zynth_verifier(settings)
    app.state.session_verifier = verifier
    app.include_router(auth_router)
    app.include_router(create_read_router(verifier))
    app.include_router(create_governance_read_router(verifier))
    app.include_router(create_write_router(verifier))
    app.include_router(create_asset_router(verifier))
    app.include_router(create_credit_router(verifier, settings.persona_credits_enabled))
    app.include_router(create_lifecycle_router(verifier, settings.persona_lifecycle_enabled))
    inspector, wrapper = photo_providers(settings)
    runtime = build_runtime(settings, inspector, wrapper)
    app.state.persona_runtime = runtime
    if settings.persona_public_passports_enabled and (
        runtime.passports is None or not runtime.passports.trust.available()
    ):
        raise ValueError("public passports require reviewed trust configuration")
    documents = None
    if settings.persona_evidence_enabled:
        if not isinstance(inspector, PillowClamdInspector) or runtime.wrapper is None:
            raise ValueError("evidence requires reviewed scanner and key providers")
        documents = DocumentInspector(inspector, inspector.scanner)
    app.include_router(
        create_evidence_router(verifier, runtime.wrapper if documents else None, documents)
    )
    app.include_router(create_passport_router(verifier, runtime.passports))
    app.include_router(create_publication_router(verifier, runtime.passports))
    app.include_router(
        create_public_passport_router(
            runtime.passports, runtime.wrapper, settings.persona_public_passports_enabled
        )
    )
    app.include_router(
        create_photo_router(
            verifier,
            inspector,
            runtime.wrapper,
            None,
            runtime.similarity,
            runtime.investigation,
        )
    )
    app.include_router(create_job_router(verifier, runtime.jobs))
    app.include_router(create_task_router(runtime.jobs, runtime.task_identity))
    app.include_router(create_runtime_router(verifier, runtime))
    app.include_router(create_assistant_router(verifier, build_provider(settings)))
    app.include_router(routes_client_events.router)

    return app


app = create_app()
