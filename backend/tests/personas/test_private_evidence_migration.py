"""Independent offline checks of frozen migration boundaries (not PostgreSQL execution)."""

from personas.test_migration_sql import render_upgrade


def test_payload_retention_and_rls_are_present_in_migration() -> None:
    sql = render_upgrade()
    assert "0007evidence" in sql
    assert "CREATE TABLE private_evidence_payloads" in sql
    assert 'ALTER TABLE "private_evidence_payloads" ENABLE ROW LEVEL SECURITY' in sql
    assert 'ALTER TABLE "private_evidence_payloads" FORCE ROW LEVEL SECURITY' in sql
    assert 'CREATE POLICY private_payload_scope ON "private_evidence_payloads"' in sql
    assert "CREATE FUNCTION accord_evidence_payload_expiry()" in sql
    assert "expires IS NULL OR expires > clock_timestamp()" in sql
    assert "CREATE TRIGGER payload_expiry BEFORE UPDATE OR DELETE" in sql
    assert "REFERENCES persona_private_evidence (workspace_id, id)" in sql
    assert "octet_length(ciphertext) BETWEEN 17 AND 10485776" in sql
