"""Explicit worker-pool configuration; existing SQL/TLS guards remain authoritative."""

import math
import os
import sys

from sqlalchemy.engine import make_url

from accord.cache.redis import validated_redis_url
from accord.config import DatabaseTransport, Environment, Settings
from accord.db.runtime import validated_database_url


def validate_compliance(settings: Settings) -> None:
    """Require the production compliance profile without activating product providers."""
    try:
        if (
            settings.environment is not Environment.PRODUCTION
            or sys.platform != "linux"
            or not os.environ.get("CLOUD_RUN_WORKER_POOL")
            or settings.database_transport is not DatabaseTransport.CLOUD_SQL_PROXY
            or settings.persona_api_enabled
            or settings.persona_photos_enabled
            or settings.persona_google_enabled
            or not math.isfinite(settings.command_poll_seconds)
            or not 1 <= settings.command_poll_seconds <= 10
        ):
            raise ValueError
        address = make_url(validated_database_url(settings, runtime=True))
        if address.username != "accord_compliance" or address.database != "appdb":
            raise ValueError
        validated_redis_url(settings)
    except Exception:
        raise ValueError("reviewed production compliance configuration required") from None
