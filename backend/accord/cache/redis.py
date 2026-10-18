"""Async Redis client + FastAPI dependency.

The telemetry emitter is **fail-open**: if Redis is unreachable, emission is swallowed and the
request still succeeds. Tests override ``get_redis`` with an in-memory fake.
"""

from __future__ import annotations

import ssl
from pathlib import Path
from urllib.parse import urlsplit

from redis.asyncio import Redis

from accord.config import Environment, Settings, get_settings

_client: Redis | None = None


def validated_redis_url(settings: Settings) -> str:
    """Require verified TLS and a mounted service CA outside local development."""
    url = settings.redis_url or "redis://localhost:6379/0"
    address = urlsplit(url)
    if (
        address.scheme not in {"redis", "rediss"}
        or not address.hostname
        or address.query
        or address.fragment
    ):
        raise ValueError("reviewed Redis address without URL options required")
    required = (
        settings.environment is not Environment.DEVELOPMENT or settings.persona_google_enabled
    )
    ca_path = settings.redis_ca_cert_path
    if address.scheme != "rediss" and (required or ca_path):
        raise ValueError("verified TLS Redis required")
    if required and not ca_path:
        raise ValueError("mounted Redis service CA required")
    if ca_path:
        if not Path(ca_path).is_absolute():
            raise ValueError("absolute Redis CA mount path required")
        try:
            ssl.create_default_context(cafile=ca_path)
        except (OSError, ValueError):
            raise ValueError("readable valid Redis service CA required") from None
    return url


def create_redis(settings: Settings, *, decode_responses: bool) -> Redis:
    """Build a disconnected client; TLS verification cannot be configured away."""
    url = validated_redis_url(settings)
    if urlsplit(url).scheme == "rediss":
        return Redis.from_url(
            url,
            decode_responses=decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
            ssl_ca_certs=settings.redis_ca_cert_path or None,
            ssl_cert_reqs="required",
            ssl_check_hostname=True,
        )
    return Redis.from_url(
        url, decode_responses=decode_responses, socket_connect_timeout=5, socket_timeout=5
    )


def get_redis() -> Redis:
    """Return a process-wide async Redis client (lazily created)."""
    global _client
    if _client is None:
        _client = create_redis(get_settings(), decode_responses=True)
    return _client
