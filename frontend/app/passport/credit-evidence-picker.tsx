import { useCallback, useState } from "react";
import type { SavedPersonaSource } from "./saved-source";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";
import type { EvidenceStatus } from "../../lib/persona-read-contracts";

type Props = {
  source: SavedPersonaSource;
  versionId: string;
  selected: string | null;
  change: (id: string | null) => void;
  label?: string;
};
export default function CreditEvidencePicker(props: Props) {
  const [open, setOpen] = useState(false);
  return (
    <div className="credit-evidence">
      {props.selected && (
        <p className="help">
          Supporting evidence selected{" "}
          <button
            type="button"
            className="text-button"
            onClick={() => props.change(null)}
          >
            Remove evidence link
          </button>
        </p>
      )}
      <button
        type="button"
        className="text-button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {open
          ? `Close ${props.label ?? "credit evidence"} picker`
          : `Choose ${props.label ?? "credit evidence"}`}
      </button>
      {open && <EvidenceChoices {...props} />}
    </div>
  );
}
function EvidenceChoices({ source, versionId, selected, change }: Props) {
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
    <div>
      <p className="help">
        Choose a reference from this version’s private evidence. Linking it does
        not share the attachment or certify the contribution.
      </p>
      <GovernanceRead
        resource="Credit evidence references"
        state={state}
        query={query}
      >
        {(page) => (
          <EvidenceItems
            items={page.items}
            selected={selected}
            change={change}
          />
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="credit evidence"
        cursor={cursor}
        next={state.phase === "ready" ? state.value.next_after_id : null}
        ready={state.phase === "ready"}
        change={(value) => {
          query.clear();
          setCursor(value as string | null);
        }}
      />
    </div>
  );
}
function EvidenceItems({
  items,
  selected,
  change,
}: {
  items: EvidenceStatus[];
  selected: string | null;
  change: (value: string) => void;
}) {
  return (
    <ul>
      {!items.length && (
        <li>
          No evidence on this page. Add supporting material in Evidence &amp;
          assets.
        </li>
      )}
      {items.map((row) => (
        <li key={row.id}>
          <button
            type="button"
            className="secondary"
            aria-pressed={selected === row.id}
            onClick={() => change(row.id)}
          >
            {row.media_type} · {row.state} · {row.id.slice(0, 8)}
          </button>
        </li>
      ))}
    </ul>
  );
}
