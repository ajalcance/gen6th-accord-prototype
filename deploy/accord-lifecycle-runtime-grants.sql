-- Prepared only; execute after reviewed migration and disposable SQL acceptance.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0018lifecycle') THEN
    RAISE EXCEPTION 'lifecycle grants require migration 0018lifecycle';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_lifecycle_records TO accord_runtime;
COMMIT;
