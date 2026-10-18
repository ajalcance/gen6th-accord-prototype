"""Optional provider assembly. Missing settings never become clean scans or default keys."""

from accord.config import Environment, Settings
from accord.personas.evidence_crypto import KeyWrapper
from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_inspector import PhotoInspector, PillowClamdInspector
from accord.personas.photo_scanner import ClamdScanner
from accord.personas.photo_vault import VaultKeyWrapper


def photo_providers(settings: Settings) -> tuple[PhotoInspector | None, KeyWrapper | None]:
    if not settings.persona_photos_enabled:
        return None, None
    if not settings.persona_api_enabled:
        raise PhotoUnavailableError("photo API requires reviewed identity activation")
    legacy = None
    if not settings.persona_google_enabled or any(
        (
            settings.photo_vault_address,
            settings.photo_vault_token.get_secret_value(),
            settings.photo_vault_key,
        )
    ):
        legacy = VaultKeyWrapper(
            settings.photo_vault_address,
            settings.photo_vault_token,
            settings.photo_vault_key,
            development=settings.environment is Environment.DEVELOPMENT,
        )
    return (
        PillowClamdInspector(ClamdScanner(port=settings.photo_clamd_port)),
        legacy,
    )
