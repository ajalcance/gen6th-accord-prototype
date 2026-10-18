import { useCallback, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";
import { GovernanceEmpty, GovernanceRead } from "./governance-common";
import { EvidenceCard } from "./evidence-card";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";

export default function SavedGovernanceEvidence({
  gateway,
  version,
}: {
  gateway: PersonaGateway;
  version: PersonaVersion;
}) {
  const [cursor, setCursor] = useState<string | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      gateway.governance.evidence(
        version.version_id,
        { after_id: cursor, limit: 20 },
        signal,
      ),
    [gateway, version.version_id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section className="governance-section" aria-label="Saved evidence status">
      <h3>Private evidence · version {version.revision}</h3>
      <p className="help">
        Owner access · metadata catalogue. Use private evidence intake on the
        saved record for upload and inspection.
      </p>
      <GovernanceRead state={state} query={query}>
        {(page) => <EvidenceItems items={page.items} />}
      </GovernanceRead>
      <DiscoveryPager
        noun="evidence"
        cursor={cursor}
        ready={state.phase === "ready"}
        next={state.phase === "ready" ? state.value.next_after_id : null}
        change={(value) => {
          query.clear();
          setCursor(value as string | null);
        }}
      />
    </section>
  );
}

function EvidenceItems({ items }: { items: EvidenceStatus[] }) {
  return (
    <>
      {items.length === 0 && (
        <GovernanceEmpty title="No evidence on this page">
          Prepare supported evidence for a verified workflow, or return to the
          first page.
        </GovernanceEmpty>
      )}
      <div className="governance-columns">
        {items.map((row) => (
          <EvidenceCard key={row.id} row={row} />
        ))}
      </div>
    </>
  );
}
