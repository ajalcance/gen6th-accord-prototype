import {
  evidenceActions,
  type EvidenceStatus,
  type WorkflowEvidence,
} from "./persona-read-contracts";
import {
  choice,
  hex,
  integer,
  object,
  requireContract,
  text,
  timestamp,
  uuid,
} from "./persona-validation";

export function parseEvidenceStatus(value: unknown): EvidenceStatus {
  const row = object(value, [
    "id",
    "workspace_id",
    "version_id",
    "media_type",
    "byte_length",
    "sha256",
    "recorded_at",
    "expires_at",
    "state",
  ]);
  const size = integer(row.byte_length);
  requireContract(size <= 10 * 1024 * 1024);
  const recorded = timestamp(row.recorded_at),
    expires = timestamp(row.expires_at);
  requireContract(Date.parse(expires) - Date.parse(recorded) === 7 * 86400000);
  return {
    id: uuid(row.id),
    workspace_id: uuid(row.workspace_id),
    version_id: uuid(row.version_id),
    media_type: choice(row.media_type, [
      "image/png",
      "image/jpeg",
      "text/plain",
    ]),
    byte_length: size,
    sha256: hex(row.sha256, 64),
    recorded_at: recorded,
    expires_at: expires,
    state: choice(row.state, ["quarantined", "clean", "rejected", "expired"]),
  };
}
function parseAnchor(value: unknown): WorkflowEvidence["anchor"] {
  const row = object(value, [
    "record_id",
    "workspace_id",
    "version_id",
    "action",
    "actor_ref",
    "recorded_at",
    "write_request_id",
    "event_id",
  ]);
  return {
    record_id: uuid(row.record_id),
    workspace_id: uuid(row.workspace_id),
    version_id: uuid(row.version_id),
    action: choice(row.action, evidenceActions),
    actor_ref: text(row.actor_ref, 64),
    recorded_at: timestamp(row.recorded_at),
    write_request_id: uuid(row.write_request_id),
    event_id: hex(row.event_id, 32),
  };
}
export function parseWorkflowEvidence(value: unknown): WorkflowEvidence {
  const row = object(value, [
    "anchor",
    "observation_request_id",
    "cold_event_present",
    "audit_state",
    "audit_sequence",
    "audit_entry_hash",
  ]);
  const state = choice(row.audit_state, ["pending", "entry_present"]);
  const sequence =
    row.audit_sequence === null ? null : integer(row.audit_sequence);
  const hash =
    row.audit_entry_hash === null ? null : hex(row.audit_entry_hash, 64);
  requireContract(typeof row.cold_event_present === "boolean");
  requireContract(
    state === "entry_present"
      ? sequence !== null && hash !== null
      : sequence === null && hash === null,
  );
  requireContract(row.cold_event_present || state === "entry_present");
  return {
    anchor: parseAnchor(row.anchor),
    observation_request_id: uuid(row.observation_request_id),
    cold_event_present: row.cold_event_present,
    audit_state: state,
    audit_sequence: sequence,
    audit_entry_hash: hash,
  };
}
