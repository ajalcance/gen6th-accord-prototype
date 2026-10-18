"""Inspection startup for the fixed production composition; no live health claims."""

from accord.config import Environment, Settings
from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.scanner_probe import probe_scanner


async def prepare_inspection(settings: Settings) -> None:
    """Finish bounded scanner readiness before non-development inspection can serve."""
    if not settings.persona_photos_enabled or settings.environment is Environment.DEVELOPMENT:
        return
    if settings.photo_clamd_port != 3310:
        raise PhotoUnavailableError("scanner readiness unavailable")
    await probe_scanner()
