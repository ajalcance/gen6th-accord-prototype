"""PostgreSQL protections for metadata-created test schemas."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from sqlalchemy import Connection, Table, event

from accord.personas.models import Persona, Version, WorkspaceMember, WriteReceipt

# Migration 0003 freezes equivalent SQL; database tests must verify both paths.
TABLES: tuple[Table, ...] = tuple(
    cast(Table, model.__table__) for model in (WorkspaceMember, Persona, Version, WriteReceipt)
)
IMMUTABLE_FUNCTION = """
CREATE FUNCTION accord_persona_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'persona versions and replay receipts are immutable';
END;
$$
"""


def policies(table_name: str) -> tuple[str, ...]:
    """Names are internal constants, never request input."""
    return (
        f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY',
        f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY',
        f'CREATE POLICY tenant_scope ON "{table_name}" '
        "USING (workspace_id = NULLIF(current_setting('accord.workspace_id', true), '')::uuid) "
        "WITH CHECK (workspace_id = "
        "NULLIF(current_setting('accord.workspace_id', true), '')::uuid)",
    )


def immutable_trigger(table_name: str) -> str:
    return (
        f'CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "{table_name}" '
        "FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()"
    )


def execute_ddl(statement: str) -> Callable[..., None]:
    """Typed schema listener for internal DDL."""

    def execute(_target: Table, connection: Connection, **_kwargs: object) -> None:
        connection.exec_driver_sql(statement)

    return execute


def register_policies() -> None:
    """Protect test schema creation identically to migration 0003."""
    for table in TABLES:
        for statement in policies(table.name):
            event.listen(table, "after_create", execute_ddl(statement))
    event.listen(Version.__table__, "after_create", execute_ddl(IMMUTABLE_FUNCTION))
    for table in TABLES[2:]:
        event.listen(table, "after_create", execute_ddl(immutable_trigger(table.name)))
    event.listen(
        Version.__table__,
        "after_drop",
        execute_ddl("DROP FUNCTION accord_persona_immutable()"),
    )
