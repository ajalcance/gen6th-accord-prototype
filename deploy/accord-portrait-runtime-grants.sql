-- Owner-only: after 0010portraits, existing accord_runtime role only.
-- No role creation, membership provisioning, cleanup or DELETE/UPDATE privileges.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0010portraits') THEN
    RAISE EXCEPTION 'portrait grants require migration 0010portraits';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_portraits, persona_portrait_payloads,
  persona_version_portraits TO accord_runtime;
COMMIT;
