-- Owner-only, after migrations, against a dedicated nonproduction database.
-- No credentials are written here. Set the password interactively with \password.
BEGIN;
CREATE ROLE accord_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO accord_runtime;
GRANT EXECUTE ON FUNCTION accord_workspace_membership(UUID, VARCHAR) TO accord_runtime;
GRANT SELECT ON persona_workspace_members, persona_identity_bindings,
  personas, persona_versions, persona_write_receipts, persona_reviews,
  persona_assets, persona_campaign_offers, persona_campaign_assets,
  persona_campaign_decisions, persona_private_evidence, persona_evidence_inspections,
  events, audit_log, detection_receipts TO accord_runtime;
GRANT INSERT, UPDATE ON personas TO accord_runtime;
GRANT INSERT ON persona_versions, persona_write_receipts, persona_reviews,
  persona_assets, persona_campaign_offers, persona_campaign_assets,
  persona_campaign_decisions, events TO accord_runtime;
COMMIT;
