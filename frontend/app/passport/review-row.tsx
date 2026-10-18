import type { ReviewReceipt } from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import GovernanceAudit from "./governance-audit";
import { RecordedTime, Unsigned } from "./governance-common";

export function ReviewRow({
  row,
  gateway,
  revision,
}: {
  row: ReviewReceipt;
  gateway: PersonaGateway;
  revision: number;
}) {
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h3>
          {row.decision === "approved"
            ? "Review approved"
            : "Changes requested"}
        </h3>
        <Unsigned />
      </div>
      <p className="help">
        Version {revision} · {row.reviewer_ref} ·{" "}
        <RecordedTime value={row.recorded_at} />
      </p>
      <p>{row.statement}</p>
      <GovernanceAudit
        gateway={gateway}
        binding={{
          recordId: row.id,
          kind: "review",
          versionId: row.version_id,
          actor: row.reviewer_ref,
          eventId: row.event_id,
          recordedAt: row.recorded_at,
        }}
      />
    </article>
  );
}
