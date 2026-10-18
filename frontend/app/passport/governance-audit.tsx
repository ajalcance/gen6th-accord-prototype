import { useState } from "react";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type {
  RecordKind,
  WorkflowEvidence,
} from "../../lib/persona-read-contracts";
import { requireContract } from "../../lib/persona-validation";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import { useGovernanceAccess } from "./saved-governance-read";

export type AuditBinding = {
  recordId: string;
  kind: RecordKind;
  versionId: string;
  actor: string;
  eventId: string;
  recordedAt: string;
};
export default function GovernanceAudit({
  gateway,
  binding,
}: {
  gateway: PersonaGateway;
  binding: AuditBinding;
}) {
  const [open, setOpen] = useState(false);
  const { state, query } = usePersonaQuery<WorkflowEvidence>();
  useGovernanceAccess(state.phase);
  function inspect() {
    setOpen(true);
    void query.run(async (signal) => {
      const evidence = await gateway.reads.workflowEvidence(
        binding.recordId,
        binding.kind,
        signal,
      );
      validateAnchor(evidence, binding);
      return evidence;
    });
  }
  return (
    <div className="governance-audit">
      <button
        className="text-button"
        aria-expanded={open}
        onClick={() => {
          if (open) {
            query.clear();
            setOpen(false);
          } else inspect();
        }}
      >
        {open ? "Close audit reference" : "Inspect audit reference"}
      </button>
      {open && (
        <>
          <ReadFeedback
            state={state}
            retry={() => void query.retry()}
            cancel={() => query.cancel()}
          />
          {state.phase === "ready" && <AuditReference evidence={state.value} />}
        </>
      )}
    </div>
  );
}

function validateAnchor(evidence: WorkflowEvidence, binding: AuditBinding) {
  const anchor = evidence.anchor;
  requireContract(
    anchor.version_id === binding.versionId &&
      anchor.actor_ref === binding.actor &&
      anchor.event_id === binding.eventId &&
      anchor.recorded_at === binding.recordedAt,
  );
}

function AuditReference({ evidence }: { evidence: WorkflowEvidence }) {
  return (
    <div className="governance-reference" role="status">
      <span className="status warning">
        {evidence.audit_state === "pending"
          ? "Audit pending"
          : "Audit entry present"}
      </span>
      <p className="help">
        {evidence.audit_state === "pending"
          ? "The event is recorded; its audit entry is pending."
          : "A matching entry is present. Chain integrity and signing are not verified here."}
      </p>
      <details>
        <summary>Reference metadata</summary>
        <dl className="governance-fields">
          <div>
            <dt>Event ID</dt>
            <dd>{evidence.anchor.event_id}</dd>
          </div>
          <div>
            <dt>Audit sequence</dt>
            <dd>{evidence.audit_sequence ?? "Pending"}</dd>
          </div>
          <div>
            <dt>Entry hash</dt>
            <dd>{evidence.audit_entry_hash ?? "Unavailable"}</dd>
          </div>
        </dl>
      </details>
    </div>
  );
}
