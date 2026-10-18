import type { DecisionReceipt } from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import GovernanceAudit from "./governance-audit";
import { RecordedTime, Unsigned } from "./governance-common";

export function DecisionRow({
  row,
  gateway,
  versionId,
}: {
  row: DecisionReceipt;
  gateway: PersonaGateway;
  versionId: string;
}) {
  const label = {
    revoked: "Revoked",
    accepted: "Accepted · historical",
    changes_requested: "Changes requested",
  }[row.decision];
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h3>{label}</h3>
        <Unsigned />
      </div>
      <p className="help">
        {row.actor_ref} · <RecordedTime value={row.recorded_at} />
      </p>
      <p>{row.statement}</p>
      <GovernanceAudit
        gateway={gateway}
        binding={{
          recordId: row.id,
          kind: "campaign_decision",
          versionId,
          actor: row.actor_ref,
          eventId: row.event_id,
          recordedAt: row.recorded_at,
        }}
      />
    </article>
  );
}
