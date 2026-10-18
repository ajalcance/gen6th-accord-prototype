import type { EvidenceStatus } from "../../lib/persona-read-contracts";
import { RecordedTime } from "./governance-common";

const STATES = {
  quarantined: {
    label: "Quarantined",
    detail: "Inspection pending. Private bytes cannot be used or downloaded.",
  },
  clean: {
    label: "Inspection passed",
    detail:
      "Temporary private evidence only. This does not grant rights or promote a campaign asset.",
  },
  rejected: {
    label: "Rejected",
    detail:
      "Inspection rejected this evidence. Replace it with a supported, safe item through a verified workflow.",
  },
  expired: {
    label: "Expired",
    detail:
      "Retention window ended; access is blocked. Expiry does not prove deletion; holds and purge policy still apply.",
  },
};

export function EvidenceCard({ row }: { row: EvidenceStatus }) {
  const info = STATES[row.state];
  return (
    <article className={`governance-card evidence-${row.state}`}>
      <div className="governance-heading">
        <h3>{info.label}</h3>
        <span className="help">
          {row.media_type} · {row.byte_length} B
        </span>
      </div>
      <p>{info.detail}</p>
      <p className="help">
        Expires <RecordedTime value={row.expires_at} />
      </p>
      <details>
        <summary>Evidence metadata</summary>
        <dl className="governance-fields">
          <div>
            <dt>Evidence ID</dt>
            <dd>{row.id}</dd>
          </div>
          <div>
            <dt>Content digest</dt>
            <dd>{row.sha256}</dd>
          </div>
          <div>
            <dt>Recorded</dt>
            <dd>
              <RecordedTime value={row.recorded_at} />
            </dd>
          </div>
        </dl>
      </details>
    </article>
  );
}
