import { useCallback, useState } from "react";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";
import type { SavedPersonaSource } from "./saved-source";
import type { WriteDraftState } from "./prepared-write-common";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";

type Props = {
  source: SavedPersonaSource;
  versionId: string;
  draft: WriteDraftState;
};
type Reference = { id: string; kind: string };
function references(value: string): Reference[] {
  return value
    .split(",")
    .filter(Boolean)
    .map((item) => {
      const [kind, id] = item.split(":");
      return { id, kind };
    });
}
export default function ProductionReferences(props: Props) {
  const [open, setOpen] = useState(false);
  const selected = references(props.draft.fields.references ?? "");
  const change = (rows: Reference[]) =>
    props.draft.change(
      "references",
      rows.map((row) => `${row.kind}:${row.id}`).join(","),
    );
  return (
    <section aria-label="Supporting references">
      <h4>
        Supporting references <small>Optional · up to 8</small>
      </h4>
      <p className="help">
        Select private evidence metadata and declare whether it supports consent
        or an ownership claim. Only its reference ID enters the offer.
      </p>
      <SelectedReferences selected={selected} change={change} />
      <button
        type="button"
        className="secondary"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {open ? "Close evidence picker" : "Choose supporting evidence"}
      </button>
      {open && (
        <ReferenceOptions {...props} selected={selected} change={change} />
      )}
    </section>
  );
}
function ReferenceOptions({
  source,
  versionId,
  selected,
  change,
}: Props & { selected: Reference[]; change: (rows: Reference[]) => void }) {
  const [cursor, setCursor] = useState<string | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.governance.evidence(
        versionId,
        { after_id: cursor, limit: 20 },
        signal,
      ),
    [source.gateway, versionId, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <div className="reference-options">
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            {!page.items.length && (
              <p>
                No evidence on this page. Add evidence to this saved version
                from Records.
              </p>
            )}
            <ul>
              {page.items.map((row) => (
                <ReferenceOption
                  key={row.id}
                  row={row}
                  selected={selected}
                  change={change}
                />
              ))}
            </ul>
          </>
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="supporting evidence"
        cursor={cursor}
        ready={state.phase === "ready"}
        next={state.phase === "ready" ? state.value.next_after_id : null}
        change={(value) => {
          query.clear();
          setCursor(value as string | null);
        }}
      />
    </div>
  );
}
function ReferenceOption({
  row,
  selected,
  change,
}: {
  row: EvidenceStatus;
  selected: Reference[];
  change: (rows: Reference[]) => void;
}) {
  const chosen = selected.find((item) => item.id === row.id);
  const [checkedAt] = useState(() => Date.now());
  const available =
    row.state === "clean" && Date.parse(row.expires_at) > checkedAt;
  return (
    <li className="reference-option">
      <p>
        {row.media_type} · {row.byte_length.toLocaleString()} bytes ·{" "}
        {row.state}
      </p>
      <p className="help">
        Recorded {new Date(row.recorded_at).toLocaleString()} · expires{" "}
        {new Date(row.expires_at).toLocaleString()}
      </p>
      <label>
        Use evidence {row.id.slice(0, 8)}
        <select
          aria-label={`Use evidence ${row.id}`}
          value={chosen?.kind ?? ""}
          disabled={!available || (!chosen && selected.length >= 8)}
          onChange={(event) =>
            change([
              ...selected.filter((item) => item.id !== row.id),
              ...(event.target.value
                ? [{ id: row.id, kind: event.target.value }]
                : []),
            ])
          }
        >
          <option value="">Not selected</option>
          <option value="consent">Consent</option>
          <option value="claim">Ownership claim</option>
        </select>
      </label>
      {!available && (
        <p className="help">
          Clean, unexpired evidence is required. The server rechecks
          availability when the offer is recorded.
        </p>
      )}
      <details>
        <summary>Inspect evidence reference</summary>
        <p className="help">ID: {row.id}</p>
        <p className="help">SHA-256: {row.sha256}</p>
      </details>
    </li>
  );
}

function SelectedReferences({
  selected,
  change,
}: {
  selected: Reference[];
  change: (rows: Reference[]) => void;
}) {
  if (!selected.length) return null;
  return (
    <ul
      className="selected-references"
      aria-label="Selected supporting references"
    >
      {selected.map((row) => (
        <li key={row.id}>
          <span>
            {row.kind === "consent" ? "Consent" : "Ownership claim"} ·{" "}
            <code>{row.id}</code>
          </span>
          <button
            type="button"
            className="text-button"
            aria-label={`Remove reference ${row.id}`}
            onClick={() =>
              change(selected.filter((item) => item.id !== row.id))
            }
          >
            Remove
          </button>
        </li>
      ))}
    </ul>
  );
}
