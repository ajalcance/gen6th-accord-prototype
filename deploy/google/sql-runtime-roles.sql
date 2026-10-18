-- SOURCE PREPARATION ONLY. Owner Cloud Shell after reviewed CI/signed release.
-- Connect explicitly to appdb as accord_migrator; never run this through a runtime.
-- No passwords or login activation. Deliberately refuses existing candidate roles.
BEGIN;
DO $$ BEGIN
  IF current_database() <> 'appdb' OR current_user <> 'accord_migrator' THEN
    RAISE EXCEPTION 'runtime role preparation requires the appdb migration operator';
  END IF;
  IF (SELECT count(*) FROM public.alembic_version) <> 1 OR
    NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = '0018lifecycle') THEN
    RAISE EXCEPTION 'runtime role preparation requires exact migration 0018lifecycle';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN
    ('accord_api', 'accord_reference', 'accord_compliance')) THEN
    RAISE EXCEPTION 'candidate role already exists; inspect instead of reconciling silently';
  END IF;
END $$;
CREATE ROLE accord_api NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE accord_reference NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE accord_compliance NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
COMMIT;
