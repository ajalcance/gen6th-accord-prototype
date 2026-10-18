"""Live integration requires a confined application role, distinct from the operator."""

from sqlalchemy import text

from accord.db.connection import _get_sessionmaker

ROLE_QUERY = """SELECT rolsuper OR rolbypassrls OR
  EXISTS (SELECT 1 FROM pg_class c WHERE pg_has_role(current_user, c.relowner, 'USAGE')
    AND (c.relname LIKE 'persona_%' OR c.relname = 'personas')) OR
  has_table_privilege(current_user, 'persona_workspace_members', 'INSERT,UPDATE,DELETE') OR
  has_table_privilege(current_user, 'persona_identity_bindings', 'INSERT,UPDATE,DELETE')
  FROM pg_roles r WHERE rolname = current_user"""


async def verify_runtime_role() -> None:
    async with _get_sessionmaker()() as session:
        unsafe = await session.scalar(text(ROLE_QUERY))
    if unsafe is not False:
        raise RuntimeError("workspace API requires a confined non-owner database role")
