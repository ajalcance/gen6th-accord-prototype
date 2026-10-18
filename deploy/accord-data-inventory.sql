-- Owner-only pre-integration inventory. Counts only; never prints content or credentials.
-- A populated store needs owner review; this script never deletes, relabels or provisions.
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '10s';
DO $inventory$
DECLARE
  item RECORD;
  rows_found BIGINT;
  domain_rows BIGINT := 0;
  tables_seen INTEGER := 0;
  flagged BIGINT;
BEGIN
  IF current_setting('transaction_read_only') <> 'on' THEN
    RAISE EXCEPTION 'inventory requires a read-only transaction';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                 AND (rolsuper OR rolbypassrls)) THEN
    RAISE EXCEPTION 'inventory requires an all-tenant operator connection';
  END IF;
  FOR item IN
    SELECT n.nspname AS schema_name, c.relname AS table_name, c.oid, c.relkind
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE c.relkind IN ('r', 'p', 'm', 'f') AND NOT c.relispartition
       AND left(n.nspname, 3) <> 'pg_' AND n.nspname <> 'information_schema'
     ORDER BY n.nspname, c.relname
  LOOP
    IF item.relkind = 'f' THEN
      RAISE EXCEPTION 'external table %.% requires provenance review; no remote rows read',
                      item.schema_name, item.table_name;
    END IF;
    EXECUTE format('SELECT count(*) FROM %I.%I', item.schema_name, item.table_name)
       INTO rows_found;
    tables_seen := tables_seen + 1;
    RAISE NOTICE 'table=%.% rows=%', item.schema_name, item.table_name, rows_found;
    IF NOT (item.schema_name = 'public' AND item.table_name = 'alembic_version') THEN
      domain_rows := domain_rows + rows_found;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = item.oid
                AND attname = 'fixture' AND NOT attisdropped AND atttypid = 'bool'::regtype) THEN
      EXECUTE format('SELECT count(*) FROM %I.%I WHERE fixture IS TRUE',
                     item.schema_name, item.table_name) INTO flagged;
      RAISE NOTICE 'table=%.% legacy_sample_rows=%', item.schema_name, item.table_name, flagged;
    END IF;
  END LOOP;
  RAISE NOTICE 'tables_checked=% non_migration_rows=%', tables_seen, domain_rows;
  IF domain_rows > 0 THEN
    RAISE EXCEPTION 'populated store requires provenance review; no rows changed';
  END IF;
  IF tables_seen = 0 THEN
    RAISE NOTICE 'inventory_result=empty_database_without_application_schema';
    RETURN;
  END IF;
  IF to_regclass('public.events') IS NULL THEN
    RAISE EXCEPTION 'Accord schema not found; check the selected database';
  END IF;
  RAISE NOTICE 'inventory_result=empty_application_store';
END $inventory$;
ROLLBACK;
