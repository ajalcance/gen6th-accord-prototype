"""The migrations must build the schema the models describe — on PostgreSQL.

Every test in this suite creates its tables from the models. Production never does that — it
runs ``alembic upgrade head``. So the whole suite can be green against a schema no deployment
will ever have, and the first sign of the gap is a migrate container failing, or worse,
succeeding against a table that is missing a column the code now writes to.

This closes that gap in both directions:

1. **The migrations apply at all.** ``upgrade head`` on an empty database, then ``downgrade
   base`` and back up, so a revision that cannot be reversed or re-applied is caught here rather
   than during an incident.
2. **The result matches the models.** Alembic's own autogenerate comparison runs against the
   migrated schema; any difference means a model changed without a migration, which is exactly
   the mistake that is invisible until deploy.

Runs on the same PostgreSQL major version as production (TA-015). Until 2026-09-25 this ran on
SQLite and could not compare column TYPES at all, because SQLite renders them differently; it
now compares types too. Differences are judged individually, never by group: alembic bundles
several changes to one column into one group, and discarding a group for one benign member
would discard the real drift beside it.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import postgres_server
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Connection, func, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from accord.db import models  # noqa: F401  (registers tables on Base.metadata)
from accord.db.base import Base
from accord.personas.database_policy import TABLES

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(url: str) -> Config:
    """Alembic wired to a throwaway database — never the developer's real one."""
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    # env.py reads this override first; see its module docstring. `%` is Alembic's
    # interpolation character, so a password containing one must be escaped.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def _flatten(differences: list[Any]) -> list[tuple[Any, ...]]:
    """Alembic yields a tuple per difference, but bundles same-column modify_* ops into a list.

    Filtering must happen on the flattened stream: classifying a bundle by its first member and
    dropping the whole bundle would silently discard real drift (say, a nullability change)
    that happens to share a column with a benign ignored difference.
    """
    flat: list[tuple[Any, ...]] = []
    for diff in differences:
        if isinstance(diff, list):
            flat.extend(diff)
        else:
            flat.append(diff)
    return flat


@pytest.fixture
def empty_database(postgres_server_url: str) -> Iterator[str]:
    """A brand-new, empty database on the session's server, dropped afterwards."""
    name = postgres_server.unique_name("accord_migrations_")
    asyncio.run(postgres_server.create_database(postgres_server_url, name))
    try:
        yield postgres_server.database_url(postgres_server_url, name)
    finally:
        asyncio.run(postgres_server.drop_database(postgres_server_url, name))


@pytest.fixture
def migrated_database(empty_database: str) -> str:
    """An empty database with `alembic upgrade head` applied to it."""
    command.upgrade(_alembic_config(empty_database), "head")
    return empty_database


def _inspect(url: str, reader: Any) -> Any:
    """Run a synchronous inspection callback against the database at `url`."""

    async def _run() -> Any:
        engine = create_async_engine(url, poolclass=NullPool)
        try:
            async with engine.connect() as connection:
                return await connection.run_sync(reader)
        finally:
            await engine.dispose()

    return asyncio.run(_run())


def test_migrations_apply_to_an_empty_database(migrated_database: str) -> None:
    """`upgrade head` created every table the models declare."""
    tables = set(_inspect(migrated_database, lambda c: inspect(c).get_table_names()))
    missing = set(Base.metadata.tables) - tables
    assert not missing, f"`alembic upgrade head` did not create: {sorted(missing)}"


def test_every_revision_can_be_reversed_and_reapplied(empty_database: str) -> None:
    """A downgrade nobody has run is a downgrade that does not work."""
    config = _alembic_config(empty_database)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    leftover = set(_inspect(empty_database, lambda c: inspect(c).get_table_names()))
    assert leftover <= {"alembic_version"}, f"`downgrade base` left tables: {sorted(leftover)}"
    command.upgrade(config, "head")


def _compare(connection: Connection) -> list[Any]:
    context = MigrationContext.configure(connection, opts={"compare_type": True})
    return _flatten(compare_metadata(context, Base.metadata))


def test_the_migrated_schema_matches_the_models(migrated_database: str) -> None:
    """A model changed without a migration is invisible until a deploy runs.

    Types, nullability, indexes and uniques are all compared, per individual difference.
    """
    differences = _inspect(migrated_database, _compare)
    assert not differences, (
        "the migrated schema does not match the models — add a migration for the model change "
        f"(or fix the migration): {differences}"
    )


def test_the_db_level_source_default_matches_the_constant(migrated_database: str) -> None:
    """The migration's server_default must be the same value the code treats as trusted.

    Three of the four homes of this value are drift-guarded (model default, SEALABLE_SOURCE,
    consumer backfill — each pinned to SOURCE_SERVER by a test); this pins the fourth, the
    default applied INSIDE the database. If it drifted, rows created outside the ORM would get
    a value the audit sealer's source filter silently excludes — an unsealed-audit gap with no
    other signal. Skips when the spine (and so the events table) is not part of this project.
    """
    envelope = pytest.importorskip(
        "accord.telemetry.envelope",
        reason="the compliance spine is not enabled in this project",
    )
    columns = _inspect(
        migrated_database, lambda c: {col["name"]: col for col in inspect(c).get_columns("events")}
    )
    # PostgreSQL reports a literal default with its cast: 'server'::character varying.
    db_default = str(columns["source"]["default"]).split("::", 1)[0].strip("'\"")
    assert db_default == envelope.SOURCE_SERVER, (
        f"events.source DB default is {db_default!r} but the code trusts "
        f"{envelope.SOURCE_SERVER!r} — rows created outside the ORM would silently escape the "
        f"audit sealer"
    )


def _persona_protections(
    connection: Connection,
) -> tuple[Sequence[Any], Sequence[Any], Sequence[Any]]:
    tables = connection.execute(
        text(
            "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
            "WHERE (relname LIKE 'persona_%' OR relname = 'personas') AND relkind = 'r' "
            "AND relnamespace = "
            "(SELECT oid FROM pg_namespace WHERE nspname = 'public')"
        )
    ).all()
    policies = connection.execute(
        text(
            "SELECT tablename, qual, with_check FROM pg_policies WHERE schemaname = 'public' "
            "AND policyname = 'tenant_scope'"
        )
    ).all()
    triggers = connection.execute(
        text(
            "SELECT c.relname, t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
            "WHERE NOT t.tgisinternal AND t.tgname = 'immutable_record'"
        )
    ).all()
    return tables, policies, triggers


def test_migration_installs_persona_protections(migrated_database: str) -> None:
    """Metadata-created test schemas cannot prove migration policy/trigger execution."""
    tables, policies, triggers = _inspect(migrated_database, _persona_protections)
    expected = {
        name for name in Base.metadata.tables if name == "personas" or name.startswith("persona_")
    }
    assert {name for name, _, _ in tables} == expected
    assert all(enabled and forced for _, enabled, forced in tables)
    assert {name for name, _, _ in policies} == expected
    assert all(
        "accord.workspace_id" in qual and "accord.workspace_id" in check
        for _, qual, check in policies
    )
    assert {name for name, _ in triggers} == expected - {"personas", "persona_workspace_members"}


def _seed_migrated_persona(connection: Connection) -> UUID:
    members, personas, versions, receipts = TABLES
    workspace, persona, version = uuid4(), uuid4(), uuid4()
    connection.execute(
        members.insert().values(
            workspace_id=workspace,
            actor_ref="fixture-creator",
            role="creator",
        )
    )
    connection.execute(
        personas.insert().values(
            id=persona,
            workspace_id=workspace,
            owner_ref="fixture-creator",
            head_revision=1,
        )
    )
    connection.execute(
        versions.insert().values(
            id=version,
            workspace_id=workspace,
            persona_id=persona,
            revision=1,
            creator_ref="fixture-creator",
            recorded_at=datetime.now(UTC),
            name="Fictional Nova",
            biography="Fictional biography",
            human_contribution="Fictional original illustration",
            ai_disclosure="Synthetic fixture",
            event_id=uuid4().hex,
        )
    )
    connection.execute(
        receipts.insert().values(
            workspace_id=workspace,
            actor_ref="fixture-creator",
            request_id=uuid4(),
            fingerprint="a" * 64,
            version_id=version,
        )
    )
    return workspace


@pytest.mark.parametrize("table_index", [2, 3])
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_migrated_immutable_records_reject_changes(
    migrated_database: str, table_index: int, operation: str
) -> None:
    def mutate(connection: Connection) -> None:
        _seed_migrated_persona(connection)
        table = TABLES[table_index]
        if operation == "delete":
            connection.execute(table.delete())
        else:
            key = "name" if table_index == 2 else "fingerprint"
            connection.execute(table.update().values(**{key: "changed"}))

    with pytest.raises(DBAPIError, match="immutable"):
        _inspect(migrated_database, mutate)


@pytest.mark.parametrize(
    "with_scope", [False, True], ids=["missing-context", "different-workspace"]
)
def test_migrated_rls_rejects_unauthorized_insert(migrated_database: str, with_scope: bool) -> None:
    def insert(connection: Connection) -> None:
        connection.execute(text("SET LOCAL ROLE pg_write_all_data"))
        if with_scope:
            connection.execute(
                text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
            )
        connection.execute(
            TABLES[0]
            .insert()
            .values(
                workspace_id=uuid4(),
                actor_ref="fixture-member",
                role="creator",
            )
        )

    with pytest.raises(DBAPIError, match="row-level security"):
        _inspect(migrated_database, insert)


def test_migrated_rls_scopes_populated_version_reads(migrated_database: str) -> None:
    def read(connection: Connection) -> tuple[int, int, int]:
        workspace = _seed_migrated_persona(connection)
        connection.execute(text("SET LOCAL ROLE pg_read_all_data"))

        def count() -> int:
            return int(connection.scalar(select(func.count()).select_from(TABLES[2])) or 0)

        missing = count()
        connection.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(uuid4())}
        )
        other = count()
        connection.execute(
            text("SELECT set_config('accord.workspace_id', :id, true)"), {"id": str(workspace)}
        )
        return missing, other, count()

    assert _inspect(migrated_database, read) == (0, 0, 1)


def test_transition_refuses_populated_sample_history(empty_database: str) -> None:
    config = _alembic_config(empty_database)
    command.upgrade(config, "0007evidence")

    def seed(connection: Connection) -> None:
        workspace, persona = uuid4(), uuid4()
        connection.execute(
            text("INSERT INTO persona_workspace_members VALUES (:w, 'creator', 'creator')"),
            {"w": workspace},
        )
        connection.execute(
            text("INSERT INTO personas VALUES (:p, :w, 'creator', 1)"),
            {"p": persona, "w": workspace},
        )
        connection.execute(
            text("""INSERT INTO persona_versions
          (id, workspace_id, persona_id, revision, creator_ref, recorded_at, name,
           biography, human_contribution, ai_disclosure, fixture, event_id)
          VALUES (:v, :w, :p, 1, 'creator', now(), 'Sample', 'Sample', 'Sample',
                  'Sample', true, :e)"""),
            {"v": uuid4(), "w": workspace, "p": persona, "e": uuid4().hex},
        )
        connection.commit()

    _inspect(empty_database, seed)
    with pytest.raises(DBAPIError, match="refuses populated history"):
        command.upgrade(config, "head")
    assert (
        _inspect(
            empty_database, lambda c: c.scalar(text("SELECT version_num FROM alembic_version"))
        )
        == "0007evidence"
    )
    assert (
        _inspect(
            empty_database,
            lambda c: c.scalar(text("SELECT count(*) FROM persona_versions WHERE fixture")),
        )
        == 1
    )


def test_real_record_rollback_refuses_populated_history(migrated_database: str) -> None:
    def seed(connection: Connection) -> None:
        _seed_migrated_persona(connection)
        connection.commit()

    _inspect(migrated_database, seed)
    with pytest.raises(DBAPIError, match="refuses populated history"):
        command.downgrade(_alembic_config(migrated_database), "0007evidence")
    assert (
        _inspect(
            migrated_database, lambda c: c.scalar(text("SELECT count(*) FROM persona_versions"))
        )
        == 1
    )
