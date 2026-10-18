"""Migration runner transport, deadlines and failure precedence without real connections."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from alembic import command

from accord.config import DatabaseTransport, Settings
from accord.db import migration_job as job


def operator_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_transport=DatabaseTransport.CLOUD_SQL_PROXY,
        database_url="postgresql+asyncpg://accord_migrator:synthetic%25@127.0.0.1:5432/appdb",
    )


def test_fixed_revision_config_preserves_encoded_credentials_and_absolute_scripts() -> None:
    value = operator_settings()
    config = job.migration_config(value, "0018lifecycle")
    assert config.get_main_option("sqlalchemy.url") == value.database_url
    assert config.get_main_option("script_location", "").endswith("/backend/migrations")
    assert config.config_file_name is None


@pytest.mark.parametrize(
    "updates,target",
    [
        ({}, "head"),
        ({}, "base"),
        ({}, "0018lifecycle;command"),
        ({"database_transport": DatabaseTransport.LOCAL}, "0018lifecycle"),
        (
            {"database_url": "postgresql+asyncpg://postgres:synthetic@127.0.0.1:5432/appdb"},
            "0018lifecycle",
        ),
        (
            {"database_url": "postgresql+asyncpg://accord_migrator:synthetic@127.0.0.1:5432/other"},
            "0018lifecycle",
        ),
        (
            {"database_url": "postgresql+asyncpg://accord_migrator:synthetic@10.42.0.3:5432/appdb"},
            "0018lifecycle",
        ),
    ],
)
def test_unreviewed_configuration_denies(updates: dict[str, object], target: str) -> None:
    with pytest.raises(ValueError):
        job.migration_config(operator_settings().model_copy(update=updates), target)


@pytest.mark.parametrize(
    "phase", [None, job.Phase.CONFIGURATION, job.Phase.STARTUP, job.Phase.MIGRATION]
)
@pytest.mark.parametrize("shutdown_failure", [False, True])
def test_every_outcome_stops_proxy_and_preserves_primary_failure(
    monkeypatch: pytest.MonkeyPatch,
    phase: job.Phase | None,
    shutdown_failure: bool,
) -> None:
    private_error = RuntimeError("synthetic-private-credential must never be reported")
    settings = Mock(return_value=operator_settings())
    startup = AsyncMock()
    upgrade = Mock()
    shutdown = AsyncMock(side_effect=private_error if shutdown_failure else None)
    if phase is job.Phase.CONFIGURATION:
        settings.side_effect = private_error
    elif phase is job.Phase.STARTUP:
        startup.side_effect = TimeoutError("synthetic timeout")
    elif phase is job.Phase.MIGRATION:
        upgrade.side_effect = private_error
    monkeypatch.setattr(job, "get_settings", settings)
    monkeypatch.setattr(job, "wait_for_proxy", startup)
    monkeypatch.setattr(command, "upgrade", upgrade)
    monkeypatch.setattr(job, "stop_proxy", shutdown)
    result = job.run_job("0018lifecycle")
    assert result.failure is phase
    assert result.shutdown_failed is shutdown_failure
    assert result.succeeded is (phase is None and not shutdown_failure)
    assert "synthetic-private-credential" not in repr(result)
    shutdown.assert_awaited_once()
    if phase in (job.Phase.CONFIGURATION, job.Phase.STARTUP):
        upgrade.assert_not_called()
    else:
        assert upgrade.call_args.args[1] == "0018lifecycle"


async def test_startup_retries_unavailable_without_redirect_or_environment_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = AsyncMock(side_effect=[503, 302, 200])
    monkeypatch.setattr(job, "proxy_request", request)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    await job.wait_for_proxy()
    assert [call.args for call in request.await_args_list] == [("startup",)] * 3


async def test_unavailable_proxy_hits_overall_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        job, "proxy_request", AsyncMock(side_effect=OSError("synthetic unavailable"))
    )
    monkeypatch.setattr(job, "STARTUP_SECONDS", 0.01)
    with pytest.raises(TimeoutError):
        await job.wait_for_proxy()


@pytest.mark.parametrize("status", [200, 302, 503])
async def test_shutdown_requires_acknowledgment_at_fixed_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
) -> None:
    request = AsyncMock(return_value=status)
    monkeypatch.setattr(job, "proxy_request", request)
    if status == 200:
        await job.stop_proxy()
    else:
        with pytest.raises(RuntimeError, match="shutdown not acknowledged"):
            await job.stop_proxy()
    request.assert_awaited_once_with("shutdown")


async def test_shutdown_deadline_bounds_a_hanging_request(monkeypatch: pytest.MonkeyPatch) -> None:
    async def handler(operation: str) -> int:
        await asyncio.sleep(1)
        return 200

    monkeypatch.setattr(job, "proxy_request", handler)
    monkeypatch.setattr(job, "SHUTDOWN_SECONDS", 0.01)
    with pytest.raises(TimeoutError):
        await job.stop_proxy()


def test_cli_reports_fixed_failure_categories_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["migration-job", "--target", "0018lifecycle"])
    monkeypatch.setattr(job, "run_job", Mock(return_value=job.JobResult(job.Phase.MIGRATION, True)))
    with pytest.raises(SystemExit) as failure:
        job.main()
    assert failure.value.code == 1
    assert (
        capsys.readouterr().out
        == "migration_job=failed\nfailure_phase=migration shutdown_failed=True\n"
    )


@pytest.mark.parametrize(
    "arguments", [[], ["--target", "head"], ["--unreviewed", "synthetic-private"]]
)
def test_invalid_cli_still_stops_proxy_without_echoing_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["migration-job", *arguments])
    monkeypatch.setattr(job, "get_settings", Mock(return_value=operator_settings()))
    shutdown = AsyncMock()
    upgrade = Mock()
    monkeypatch.setattr(job, "stop_proxy", shutdown)
    monkeypatch.setattr(command, "upgrade", upgrade)
    with pytest.raises(SystemExit) as failure:
        job.main()
    assert failure.value.code == 1
    output = capsys.readouterr()
    assert "failure_phase=configuration" in output.out
    assert "synthetic-private" not in output.out + output.err
    shutdown.assert_awaited_once()
    upgrade.assert_not_called()
