-- Owner-only after reviewed 0013investigation. No keys, models or live calls are activated.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0013investigation') THEN
    RAISE EXCEPTION 'investigation grants require migration 0013investigation';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_investigations TO accord_runtime;
GRANT SELECT, INSERT ON persona_investigation_review_requests TO accord_runtime;
COMMIT;
