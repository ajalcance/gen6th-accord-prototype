"""Fail before any grants when schema, role attributes or inherited authority are wrong."""

from typing import Any

import pytest


@pytest.mark.parametrize("filename", ["sql-runtime-roles.sql", "sql-runtime-grants.sql"])
async def test_exact_head_required(prepared_roles: Any, filename: str) -> None:
    db = prepared_roles.connection
    await db.execute("BEGIN")
    await db.execute("UPDATE alembic_version SET version_num = '0017credits'")
    with pytest.raises(Exception, match="exact migration 0018lifecycle") as error:
        await db.execute(prepared_roles.script(filename))
    assert getattr(error.value, "sqlstate", None) == "P0001"
    await db.execute("ROLLBACK")


async def test_existing_roles_are_not_recreated(prepared_roles: Any) -> None:
    with pytest.raises(Exception, match="candidate role already exists") as error:
        await prepared_roles.connection.execute(prepared_roles.script("sql-runtime-roles.sql"))
    assert getattr(error.value, "sqlstate", None) == "P0001"
    await prepared_roles.connection.execute("ROLLBACK")


async def test_creator_admin_membership_is_permitted(prepared_roles: Any) -> None:
    db = prepared_roles.connection
    operator = await db.fetchval("SELECT current_user")
    role = prepared_roles.roles["api"]
    await db.execute(f'GRANT "{role}" TO "{operator}" WITH ADMIN TRUE, INHERIT FALSE, SET FALSE')
    await db.execute(prepared_roles.script("sql-runtime-grants.sql"))
    assert await db.fetchval("SELECT has_table_privilege($1, 'personas', 'INSERT')", role) is True


@pytest.mark.parametrize(
    "unsafe",
    ["LOGIN", "SUPERUSER", "BYPASSRLS", "CREATEDB", "CREATEROLE", "REPLICATION", "INHERIT"],
)
async def test_unsafe_attributes_refuse_grants(prepared_roles: Any, unsafe: str) -> None:
    db = prepared_roles.connection
    await db.execute("BEGIN")
    await db.execute(f'ALTER ROLE "{prepared_roles.roles["api"]}" {unsafe}')
    with pytest.raises(Exception, match="unactivated, unprivileged nonowners") as error:
        await db.execute(prepared_roles.script("sql-runtime-grants.sql"))
    assert getattr(error.value, "sqlstate", None) == "P0001"
    await db.execute("ROLLBACK")


@pytest.mark.parametrize(
    "authority",
    [
        "membership",
        "ownership",
        "grant",
        "third-party",
        "operator-without-admin",
        "operator-inherits",
    ],
)
async def test_membership_ownership_or_prior_acl_refuses_grants(
    prepared_roles: Any, authority: str
) -> None:
    db, role = prepared_roles.connection, prepared_roles.roles["api"]
    operator = await db.fetchval("SELECT current_user")
    reference = prepared_roles.roles["reference"]
    statements = {
        "membership": f'GRANT pg_read_all_data TO "{role}"',
        "ownership": f'ALTER TABLE personas OWNER TO "{role}"',
        "grant": f'GRANT DELETE ON events TO "{role}"',
        "third-party": f'GRANT "{role}" TO "{reference}" WITH ADMIN OPTION',
        "operator-without-admin": f'GRANT "{role}" TO "{operator}" WITH ADMIN FALSE',
        "operator-inherits": f'GRANT "{role}" TO "{operator}" WITH ADMIN TRUE, INHERIT TRUE',
    }
    await db.execute("BEGIN")
    await db.execute(statements[authority])
    with pytest.raises(Exception, match="unactivated, unprivileged nonowners") as error:
        await db.execute(prepared_roles.script("sql-runtime-grants.sql"))
    assert getattr(error.value, "sqlstate", None) == "P0001"
    await db.execute("ROLLBACK")
