-- Owner-only after reviewed 0012faces; does not activate models, keys, migrations or cloud calls.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0012faces') THEN
    RAISE EXCEPTION 'face grants require migration 0012faces';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_face_generations TO accord_runtime;
COMMIT;
