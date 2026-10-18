-- Owner-only after reviewed 0015jobs. No credentials, grants execution or cloud activation.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0015jobs') THEN
    RAISE EXCEPTION 'job grants require migration 0015jobs';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_face_jobs, persona_face_job_transitions TO accord_runtime;
COMMIT;
