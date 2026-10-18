"""Production ASGI factory bound directly to the real managed runtime."""

from fastapi import FastAPI

from accord.scanner.app import create_scanner_app
from accord.scanner.runtime import ScannerRuntime


def create_app() -> FastAPI:
    return create_scanner_app(ScannerRuntime())
