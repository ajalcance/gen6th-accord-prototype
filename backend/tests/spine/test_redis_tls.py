"""Real Redis TLS context configuration without sockets, credentials or cloud resources."""

import ssl
from pathlib import Path
from unittest.mock import Mock

import pytest
from redis.asyncio import Redis
from redis.asyncio.connection import SSLConnection
from redis_fixtures import service_ca

from accord.cache import redis as cache
from accord.config import Environment, Settings


def production(ca_path: Path | None = None) -> Settings:
    return Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        secret_key="synthetic-session-key",
        database_url="postgresql+asyncpg://synthetic-db/app",
        redis_url="rediss://synthetic-redis:6378/0",
        redis_ca_cert_path=str(ca_path) if ca_path else "",
    )


@pytest.mark.parametrize("decode_responses", [True, False])
def test_real_tls_context_requires_peer_and_hostname_verification(
    tmp_path: Path, decode_responses: bool
) -> None:
    path = service_ca(tmp_path)
    client = cache.create_redis(production(path), decode_responses=decode_responses)
    pool = client.connection_pool
    assert pool.connection_class is SSLConnection
    connection = SSLConnection(**pool.connection_kwargs)
    context = connection.ssl_context.get()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    assert pool.connection_kwargs["ssl_ca_certs"] == str(path)
    assert pool.connection_kwargs["decode_responses"] is decode_responses
    assert ssl.PEM_cert_to_DER_cert(path.read_text()) in context.get_ca_certs(binary_form=True)


@pytest.mark.parametrize(
    "changes",
    [
        {"redis_url": ""},
        {"redis_url": "redis://synthetic-redis:6379/0"},
        {"redis_url": "rediss://synthetic-redis:6378/0?ssl_cert_reqs=none"},
        {"redis_url": "rediss://synthetic-redis:6378/0?ssl_check_hostname=false"},
        {"redis_url": "rediss://synthetic-redis:6378/0#options"},
        {"redis_ca_cert_path": ""},
        {"redis_ca_cert_path": "relative-ca.crt"},
    ],
)
def test_invalid_production_config_never_constructs_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, changes: dict[str, object]
) -> None:
    create = Mock(side_effect=AssertionError("invalid config must not construct a client"))
    monkeypatch.setattr(Redis, "from_url", create)
    with pytest.raises(ValueError):
        cache.create_redis(
            production(service_ca(tmp_path)).model_copy(update=changes), decode_responses=True
        )
    create.assert_not_called()


@pytest.mark.parametrize("exists", [False, True])
def test_missing_or_malformed_ca_denies_without_exposing_path(tmp_path: Path, exists: bool) -> None:
    path = tmp_path / "not-a-ca.crt"
    if exists:
        path.write_text("synthetic malformed certificate")
    with pytest.raises(ValueError, match="^readable valid Redis service CA required$"):
        cache.create_redis(production(path), decode_responses=True)


def test_compliance_client_uses_same_verified_factory_and_is_cached(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cache, "_client", None)
    monkeypatch.setattr(cache, "get_settings", lambda: production(service_ca(tmp_path)))
    first = cache.get_redis()
    assert cache.get_redis() is first
    assert first.connection_pool.connection_kwargs["ssl_check_hostname"] is True
    assert first.connection_pool.connection_kwargs["decode_responses"] is True


def test_plaintext_default_is_only_available_to_local_development() -> None:
    client = cache.create_redis(Settings(_env_file=None), decode_responses=True)
    assert client.connection_pool.connection_kwargs["host"] == "localhost"
    with pytest.raises(ValueError, match="TLS Redis required"):
        cache.create_redis(
            Settings(_env_file=None, persona_google_enabled=True), decode_responses=False
        )
