"""Build only the reviewed Zynth verifier; absent configuration remains unavailable."""

from accord.auth.browser_oidc import BrowserOidc, app_origin
from accord.auth.browser_store import BrowserStore
from accord.auth.zynth_http import ZynthHttp, ZynthSettings
from accord.auth.zynth_session import ZynthSessionVerifier
from accord.cache.redis import get_redis
from accord.config import Environment, Settings
from accord.personas.identity_repository import resolve_identity


def build_zynth_verifier(settings: Settings) -> BrowserOidc | None:
    if not settings.persona_api_enabled:
        return None
    if not settings.zynth_tenant_id or not settings.persona_workspace_id:
        raise ValueError("Zynth tenant and Accord workspace must be configured")
    config = ZynthSettings(issuer=settings.zynth_issuer, client_id=settings.zynth_client_id)
    required = (settings.zynth_client_secret, settings.database_url, settings.redis_url)
    if not all(required):
        raise ValueError("Zynth connection requires confidential client, database and Redis config")
    origin, _ = app_origin(
        settings.accord_app_origin, settings.environment is Environment.DEVELOPMENT
    )
    store = BrowserStore(
        get_redis(), settings.zynth_session_key, f"{config.issuer}:{config.client_id}"
    )
    verifier = ZynthSessionVerifier(
        config,
        ZynthHttp(config),
        settings.zynth_tenant_id,
        settings.persona_workspace_id,
        resolve_identity,
    )
    return BrowserOidc(config, settings.zynth_client_secret, origin, store, verifier)
