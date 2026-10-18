-- Owner-only after reviewed 0016passports; no execution or credentials in this source slice.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '0016passports') THEN
    RAISE EXCEPTION 'passport grants require migration 0016passports';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accord_runtime'
    AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole) THEN
    RAISE EXCEPTION 'confined accord_runtime role required';
  END IF;
END $$;
GRANT SELECT, INSERT ON persona_assets, persona_asset_enrollments, persona_passport_issuances,
  persona_passport_publications, persona_passport_unpublications TO accord_runtime;
-- Evidence tables already have scoped SELECT/INSERT in the reviewed runtime grants.
-- No DELETE grant: retention authority is not configured and no cleanup is activated.
COMMIT;
