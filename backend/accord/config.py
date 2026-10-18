"""Application settings.

Settings load from environment variables / ``.env``. Secrets default to empty and
the app **fails closed**: outside ``development`` the validator *requires* real secrets
and raises if any are missing — there is no insecure fallback.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from uuid import UUID

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseTransport(StrEnum):
    LOCAL = "local"
    CLOUD_SQL_PROXY = "cloud_sql_proxy"


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "info"

    # --- Secrets (required outside development — fail closed) ---
    secret_key: str = ""
    database_url: str = ""
    database_transport: DatabaseTransport = DatabaseTransport.LOCAL

    # Disabled integration denies requests; no implicit identity or role grant.
    persona_api_enabled: bool = False
    zynth_issuer: str = ""
    zynth_client_id: str = ""
    zynth_tenant_id: UUID | None = None
    persona_workspace_id: UUID | None = None
    zynth_client_secret: str = ""
    zynth_session_key: str = ""
    accord_app_origin: str = ""
    persona_photos_enabled: bool = False
    persona_evidence_enabled: bool = False
    persona_credits_enabled: bool = False
    persona_lifecycle_enabled: bool = False
    persona_public_passports_enabled: bool = False
    photo_clamd_port: int = 3310
    photo_vault_address: str = ""
    photo_vault_token: SecretStr = SecretStr("")
    photo_vault_key: str = ""
    persona_google_enabled: bool = False
    persona_google_config: str = ""
    # Advisory reviewer brief (ADR-0074): text-only Gemini on Vertex AI, off unless enabled.
    persona_assistant_enabled: bool = False
    persona_assistant_project: str = ""
    persona_assistant_region: str = "global"
    persona_assistant_model: str = "gemini-3.8-flash"

    # --- Compliance/observability spine ---
    redis_url: str = ""
    redis_ca_cert_path: str = ""
    telemetry_enabled: bool = True
    telemetry_stream: str = "gen6th-accord:events"
    telemetry_stream_maxlen: int = 20_000
    command_retention_days: int = 30
    command_poll_seconds: float = 2.0
    # X-Forwarded-For is an ordinary request header any caller can send. Enable this ONLY when
    # a trusted reverse proxy (the deploy module's Caddy) fronts the service; the recorded
    # client IP then comes from the hop the proxy appended, never one the caller supplied.
    # Default False = fail closed: without a proxy, the peer address is the only IP the server
    # itself observed. See telemetry/envelope.py:client_ip and ADR-0012.
    trust_x_forwarded_for: bool = False

    @field_validator("zynth_tenant_id", "persona_workspace_id", mode="before")
    @classmethod
    def absent_integration_id(cls, value: object) -> object:
        return None if value == "" else value

    @property
    def is_production(self) -> bool:
        """Whether the app is running in the production environment."""
        return self.environment is Environment.PRODUCTION

    @model_validator(mode="after")
    def _require_config_outside_dev(self) -> Settings:
        """Fail closed: required secrets/config must be present outside development."""
        if self.environment is not Environment.DEVELOPMENT:
            required = ("secret_key", "database_url")
            missing = [name for name in required if not getattr(self, name)]
            if missing:
                raise ValueError(
                    f"Missing required config in {self.environment.value}: " + ", ".join(missing)
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
