"""Health-only factory. Required runtime is supplied by later reviewed packaging."""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from accord.scanner.processes import ManagedRuntime
from accord.scanner.supervisor import ScannerSupervisor


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    supervisor: ScannerSupervisor = app.state.scanner
    supervisor.start()
    try:
        yield  # Native startup must be able to observe starting/503 while bootstrap runs.
    finally:
        await supervisor.stop()


def create_scanner_app(runtime: ManagedRuntime) -> FastAPI:
    if sys.platform != "linux" or os.geteuid() == 0:
        raise ValueError("scanner platform unavailable")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    supervisor = ScannerSupervisor(runtime)
    app.state.scanner = supervisor

    @app.get("/health")
    async def health() -> JSONResponse:
        state = supervisor.health()
        return JSONResponse(
            {"status": state, "scope": "scanner_protocol_freshness"},
            status_code=200 if state == "ready" else 503,
            headers={"Cache-Control": "no-store"},
        )

    return app
