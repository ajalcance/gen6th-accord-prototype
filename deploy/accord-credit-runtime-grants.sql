-- Owner-only preparation after reviewed 0017credits; execution is separately authorized.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0017credits') THEN
    RAISE EXCEPTION 'credit grants require migration 0017credits';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_credit_profiles, persona_credit_confirmations TO accord_runtime;
COMMIT;
