-- Owner-only after reviewed 0011captures; does not run migrations, create roles or activate providers.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0011captures') THEN
    RAISE EXCEPTION 'capture grants require migration 0011captures';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_portraits, persona_portrait_payloads,
  persona_version_portraits, persona_portrait_captures, persona_version_references TO accord_runtime;
COMMIT;
