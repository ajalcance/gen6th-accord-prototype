"""Tenant confinement and immutable asset enrollment provenance."""

from typing import cast

from sqlalchemy import Table, event

from accord.personas.asset_models import AssetEnrollment
from accord.personas.database_policy import execute_ddl, immutable_trigger, policies


def register_enrollment_policy() -> None:
    table = cast(Table, AssetEnrollment.__table__)
    for statement in (*policies(table.name), immutable_trigger(table.name)):
        event.listen(table, "after_create", execute_ddl(statement))
