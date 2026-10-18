-- SOURCE PREPARATION ONLY. Separately reviewed owner checkpoint, not deployment automation.
-- Requires the freshly prepared NOLOGIN roles and exact schema head. No default grants.
BEGIN;
DO $$ DECLARE candidate record; BEGIN
  IF current_database() <> 'appdb' OR current_user <> 'accord_migrator' THEN
    RAISE EXCEPTION 'runtime grants require the appdb migration operator';
  END IF;
  IF (SELECT count(*) FROM public.alembic_version) <> 1 OR
    NOT EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = '0018lifecycle') THEN
    RAISE EXCEPTION 'runtime grants require exact migration 0018lifecycle';
  END IF;
  IF (SELECT count(*) FROM pg_roles WHERE rolname IN
    ('accord_api', 'accord_reference', 'accord_compliance')) <> 3 THEN
    RAISE EXCEPTION 'all three prepared roles are required';
  END IF;
  FOR candidate IN SELECT * FROM pg_roles WHERE rolname IN
    ('accord_api', 'accord_reference', 'accord_compliance') LOOP
    IF candidate.rolsuper OR candidate.rolbypassrls OR candidate.rolcreatedb OR
      candidate.rolcreaterole OR candidate.rolreplication OR candidate.rolinherit OR
      candidate.rolcanlogin OR EXISTS (SELECT 1 FROM pg_auth_members
        WHERE member = candidate.oid OR (roleid = candidate.oid AND
          (member <> (SELECT oid FROM pg_roles WHERE rolname = current_user)
            OR NOT admin_option OR inherit_option OR set_option))) OR
      EXISTS (SELECT 1 FROM pg_shdepend WHERE refclassid = 'pg_authid'::regclass
        AND refobjid = candidate.oid AND deptype IN ('o', 'a')) OR
      EXISTS (SELECT 1 FROM pg_class WHERE relnamespace = 'public'::regnamespace
        AND relkind IN ('r', 'p') AND
        has_any_column_privilege(candidate.rolname, oid, 'SELECT,INSERT,UPDATE,REFERENCES')) THEN
      RAISE EXCEPTION 'candidate roles must be unactivated, unprivileged nonowners';
    END IF;
  END LOOP;
END $$;
-- PUBLIC privileges are additive: NOINHERIT does not exclude them. Close DDL/temp access
-- for this application database. CONNECT and schema USAGE remain compatible with operators.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE TEMPORARY ON DATABASE appdb FROM PUBLIC;
GRANT CONNECT ON DATABASE appdb TO accord_api, accord_reference, accord_compliance;
GRANT USAGE ON SCHEMA public TO accord_api, accord_reference, accord_compliance;

GRANT SELECT ON persona_workspace_members, persona_identity_bindings TO accord_api;
GRANT SELECT, INSERT ON personas, persona_versions, persona_write_receipts,
  persona_reviews, persona_portraits, persona_portrait_payloads, persona_version_portraits,
  persona_portrait_captures, persona_version_references, persona_face_generations,
  persona_assets, persona_campaign_offers, persona_campaign_assets, persona_campaign_decisions,
  persona_private_evidence, private_evidence_payloads, persona_evidence_inspections,
  persona_investigations, persona_investigation_review_requests,
  persona_face_jobs, persona_face_job_transitions, persona_asset_enrollments,
  persona_passport_issuances, persona_passport_publications, persona_passport_unpublications,
  persona_credit_profiles, persona_credit_confirmations, persona_lifecycle_records TO accord_api;
GRANT UPDATE (head_revision) ON personas TO accord_api;
-- SELECT FOR UPDATE needs a column UPDATE grant; immutable_record still rejects mutation.
GRANT UPDATE (id) ON persona_private_evidence, persona_passport_publications TO accord_api;
GRANT SELECT, INSERT ON events TO accord_api;
GRANT SELECT ON audit_log, detection_receipts TO accord_api;
GRANT EXECUTE ON FUNCTION accord_workspace_membership(uuid, character varying) TO accord_api;

GRANT SELECT ON personas, persona_versions, persona_portraits, persona_portrait_captures,
  persona_version_references, persona_face_jobs, persona_face_job_transitions,
  persona_face_generations TO accord_reference;
-- The worker locks the mutable head. This grants real head-write authority, not lock-only.
GRANT UPDATE (head_revision) ON personas TO accord_reference;
GRANT INSERT ON persona_face_job_transitions, persona_face_generations, events TO accord_reference;
GRANT EXECUTE ON FUNCTION accord_workspace_membership(uuid, character varying) TO accord_reference;

GRANT SELECT, INSERT, DELETE ON events TO accord_compliance;
GRANT SELECT, INSERT ON audit_log, detection_receipts TO accord_compliance;
GRANT USAGE ON SEQUENCE audit_log_seq_seq TO accord_compliance;
-- No metadata provisioning, original-payload deletion, blanket UPDATE, ownership or DDL.
-- Compliance event DELETE is table-wide authority; the existing worker enforces retention.
COMMIT;
