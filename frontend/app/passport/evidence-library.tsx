import { useEffect, useState } from "react";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type { EvidenceGateway } from "../../lib/persona-evidence";
import type { AssetRegistry } from "../../lib/persona-assets";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";
import { usePersonaQuery } from "./use-persona-query";
import { useGovernanceAccess } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";
import AssetEnrollment from "./asset-enrollment";
import EvidenceDownload from "./evidence-download";

type Page = Awaited<ReturnType<PersonaGateway["governance"]["evidence"]>>;
export default function EvidenceLibrary({
  records,
  gateway,
  registry,
  versionId,
  denied,
  purgeAvailable,
}: {
  records: PersonaGateway;
  gateway: EvidenceGateway;
  registry?: AssetRegistry;
  versionId: string;
  denied: () => void;
  purgeAvailable: boolean;
}) {
  const { state, query } = usePersonaQuery<Page>();
  const [cursor, setCursor] = useState<string | null>(null);
  useGovernanceAccess(state.phase);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  const load = (after: string | null) =>
    void query.run((signal) =>
      records.governance.evidence(
        versionId,
        { after_id: after, limit: 20 },
        signal,
      ),
    );
  return (
    <section aria-label="Existing private evidence">
      <h4>Saved evidence for this version</h4>
      <button disabled={state.phase === "loading"} onClick={() => load(cursor)}>
        Refresh saved evidence
      </button>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            {page.items.length === 0 && (
              <p>No private evidence on this page.</p>
            )}
            {page.items.map((row) => (
              <EvidenceActions
                key={`${row.id}:${row.state}:${row.expires_at}`}
                row={row}
                gateway={gateway}
                registry={registry}
                denied={denied}
                purgeAvailable={purgeAvailable}
              />
            ))}
            <button
              disabled={cursor === null}
              onClick={() => {
                setCursor(null);
                load(null);
              }}
            >
              First evidence page
            </button>
            <button
              disabled={page.next_after_id === null}
              onClick={() => {
                setCursor(page.next_after_id);
                load(page.next_after_id);
              }}
            >
              Next evidence page
            </button>
          </>
        )}
      </GovernanceRead>
    </section>
  );
}
function EvidenceActions({
  row: initial,
  gateway,
  registry,
  denied,
  purgeAvailable,
}: {
  row: EvidenceStatus;
  gateway: EvidenceGateway;
  registry?: AssetRegistry;
  denied: () => void;
  purgeAvailable: boolean;
}) {
  const { state, query } = usePersonaQuery<EvidenceStatus>();
  useGovernanceAccess(state.phase);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  const row = state.phase === "ready" ? state.value : initial;
  const [download, setDownload] = useState<Blob | null>(null);
  return (
    <article className="governance-section">
      <p>
        {row.media_type} · {row.byte_length} bytes · {row.state} · expires{" "}
        {row.expires_at}
      </p>
      <details>
        <summary>Evidence reference</summary>
        <p>{row.id}</p>
        <p>SHA-256: {row.sha256}</p>
      </details>
      <button
        disabled={row.state !== "quarantined" || state.phase === "loading"}
        onClick={() =>
          void query.run((signal) => gateway.inspect(row.id, signal))
        }
      >
        Inspect saved evidence
      </button>
      <button
        disabled={row.state !== "clean" || state.phase === "loading"}
        onClick={() =>
          void query.run(async (signal) => {
            const blob = await gateway.download(row, signal);
            if (!signal.aborted) setDownload(blob);
            return row;
          })
        }
      >
        Prepare private download
      </button>
      <button
        disabled={
          row.state !== "expired" ||
          !purgeAvailable ||
          state.phase === "loading"
        }
        onClick={() =>
          void query.run((signal) => gateway.purge(row.id, signal))
        }
      >
        Purge expired payload
      </button>
      {!purgeAvailable && (
        <p className="help">
          Deletion requires configured retention authority. Expiry prevents
          access; it does not certify physical deletion.
        </p>
      )}
      <GovernanceRead state={state} query={query}>
        {() => download && <EvidenceDownload blob={download} id={row.id} />}
      </GovernanceRead>
      {row.state === "clean" && registry && (
        <AssetEnrollment
          key={row.id}
          registry={registry}
          row={row}
          denied={denied}
        />
      )}
    </article>
  );
}
