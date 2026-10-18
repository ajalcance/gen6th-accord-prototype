"""Metadata is immutable; encrypted payload deletion is allowed only after expiry."""

from sqlalchemy import event

from accord.personas.database_policy import execute_ddl, immutable_trigger, policies
from accord.personas.evidence_models import EvidenceInspection, EvidencePayload, PrivateEvidence

PAYLOAD_FUNCTION = """
CREATE FUNCTION accord_evidence_payload_expiry() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expires TIMESTAMP WITH TIME ZONE;
BEGIN
    IF TG_OP <> 'DELETE' THEN
        RAISE EXCEPTION 'encrypted payload is immutable';
    END IF;
    SELECT expires_at INTO expires FROM persona_private_evidence
        WHERE id = OLD.evidence_id AND workspace_id = OLD.workspace_id;
    IF expires IS NULL OR expires > clock_timestamp() THEN
        RAISE EXCEPTION 'encrypted payload has not expired';
    END IF;
    RETURN OLD;
END;
$$
"""
PAYLOAD_TRIGGER = """CREATE TRIGGER payload_expiry BEFORE UPDATE OR DELETE
ON private_evidence_payloads FOR EACH ROW EXECUTE FUNCTION accord_evidence_payload_expiry()"""


def register_evidence_policies() -> None:
    for model in (PrivateEvidence, EvidenceInspection, EvidencePayload):
        for statement in policies(model.__tablename__):
            if model is EvidencePayload:
                statement = statement.replace("POLICY tenant_scope", "POLICY private_payload_scope")
            event.listen(model.__table__, "after_create", execute_ddl(statement))
    for model in (PrivateEvidence, EvidenceInspection):
        event.listen(
            model.__table__, "after_create", execute_ddl(immutable_trigger(model.__tablename__))
        )
    for statement in (PAYLOAD_FUNCTION, PAYLOAD_TRIGGER):
        event.listen(EvidencePayload.__table__, "after_create", execute_ddl(statement))
    event.listen(
        EvidencePayload.__table__,
        "after_drop",
        execute_ddl("DROP FUNCTION accord_evidence_payload_expiry()"),
    )
