"""Forced tenant isolation and immutable identity bindings for metadata-created schemas."""

from sqlalchemy import event

from accord.personas.database_policy import execute_ddl, policies
from accord.personas.identity_models import IdentityBinding

IMMUTABLE = """CREATE FUNCTION accord_identity_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'identity bindings are immutable'; END; $$"""
TRIGGER = """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON persona_identity_bindings
FOR EACH ROW EXECUTE FUNCTION accord_identity_immutable()"""
MEMBERSHIP_LOCK = """CREATE FUNCTION accord_workspace_membership(w UUID, a VARCHAR)
RETURNS VARCHAR LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE result VARCHAR;
BEGIN
  IF w IS DISTINCT FROM NULLIF(current_setting('accord.workspace_id', true), '')::uuid THEN
    RETURN NULL;
  END IF;
  SELECT role INTO result FROM public.persona_workspace_members
    WHERE workspace_id = w AND actor_ref = a FOR UPDATE;
  RETURN result;
END; $$"""


def register_identity_policy() -> None:
    table = IdentityBinding.__table__
    for statement in (
        *policies("persona_identity_bindings"),
        IMMUTABLE,
        TRIGGER,
        MEMBERSHIP_LOCK,
        "REVOKE ALL ON FUNCTION accord_workspace_membership(UUID, VARCHAR) FROM PUBLIC",
    ):
        event.listen(table, "after_create", execute_ddl(statement))
    event.listen(
        table, "after_drop", execute_ddl("DROP FUNCTION accord_workspace_membership(UUID, VARCHAR)")
    )
    event.listen(table, "after_drop", execute_ddl("DROP FUNCTION accord_identity_immutable()"))
