import { EvidenceCard } from "../../app/passport/evidence-card";
import { useEffect } from "react";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";
import { requireContract } from "../../lib/persona-validation";
import {
  EXAMPLE_EVIDENCE,
  EXAMPLE_REVIEW_VERSION,
} from "./governance-fixtures";
import {
  GovernanceEmpty,
  GovernanceRead,
} from "../../app/passport/governance-common";
import { usePersonaQuery } from "../../app/passport/use-persona-query";

export default function GovernanceEvidence({
  gateway,
  empty,
}: {
  gateway: PersonaGateway;
  empty: boolean;
}) {
  const { state, query } = useEvidenceStatuses(gateway, empty);
  if (empty)
    return (
      <GovernanceEmpty title="No evidence attached">
        Prepare a supported PNG, JPEG or plain-text item, up to 10 MiB. Upload
        requires a verified connection; no upload service is active here.
      </GovernanceEmpty>
    );
  return (
    <section className="governance-section" aria-label="Evidence status">
      <h3>Private evidence status</h3>
      <p className="help">
        Version 2 · metadata only · seven-day payload retention. No files,
        private contents, key handles or download links are exposed.
      </p>
      <GovernanceRead state={state} query={query}>
        {(rows) => (
          <div className="governance-columns">
            {rows.map((row) => (
              <EvidenceCard key={row.id} row={row} />
            ))}
          </div>
        )}
      </GovernanceRead>
    </section>
  );
}

function useEvidenceStatuses(gateway: PersonaGateway, empty: boolean) {
  const read = usePersonaQuery<EvidenceStatus[]>();
  const { query } = read;
  useEffect(() => {
    if (!empty)
      void query.run((signal) =>
        Promise.all(
          EXAMPLE_EVIDENCE.map(async ({ id }) => {
            const row = await gateway.reads.evidenceStatus(id, signal);
            requireContract(
              row.version_id === EXAMPLE_REVIEW_VERSION.version_id,
            );
            return row;
          }),
        ),
      );
    return () => query.clear();
  }, [gateway, empty, query]);
  return read;
}

export { EvidenceCard } from "../../app/passport/evidence-card";
