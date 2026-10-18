"""Tenant RLS and append-only issuance, publication approval and unpublication."""

from typing import cast

from sqlalchemy import Table, event

from accord.personas.database_policy import execute_ddl, immutable_trigger, policies
from accord.personas.issuance_models import (
    PassportIssuance,
    PassportPublication,
    PassportUnpublication,
)


def register_issuance_policy() -> None:
    for model in (PassportIssuance, PassportPublication, PassportUnpublication):
        table = cast(Table, model.__table__)
        for statement in (*policies(table.name), immutable_trigger(table.name)):
            event.listen(table, "after_create", execute_ddl(statement))
