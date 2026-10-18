"""Test-schema protections for immutable review rows; migration 0004 freezes SQL."""

from typing import cast

from sqlalchemy import Table, event

from accord.personas.database_policy import execute_ddl, immutable_trigger, policies
from accord.personas.review_models import ReviewRecord

REVIEW_TABLES: tuple[Table, ...] = (cast(Table, ReviewRecord.__table__),)


def register_review_policies() -> None:
    for table in REVIEW_TABLES:
        for statement in (*policies(table.name), immutable_trigger(table.name)):
            event.listen(table, "after_create", execute_ddl(statement))
