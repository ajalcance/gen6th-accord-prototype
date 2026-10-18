import { useCallback, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { useGovernanceRead, DiscoveryPager } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";

export default function RecordVersionPicker({
  source,
  version,
  choose,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  choose: (revision: number | null) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="record-version-picker">
      <button
        className="secondary"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        Version {version.revision} · Change version
      </button>
      {open && (
        <VersionChoices source={source} version={version} choose={choose} />
      )}
    </div>
  );
}

function VersionChoices({
  source,
  version,
  choose,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  choose: (revision: number | null) => void;
}) {
  const [cursor, setCursor] = useState<number | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.governance.versions(
        version.persona_id,
        { before_revision: cursor, limit: 20 },
        signal,
      ),
    [source.gateway, version.persona_id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section
      aria-label="Choose saved version"
      className="record-version-choices"
    >
      <button className="secondary" onClick={() => choose(null)}>
        Load current version
      </button>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <ul>
            {page.items.map((item) => (
              <li key={item.version_id}>
                <button
                  className="text-button"
                  onClick={() => choose(item.revision)}
                >
                  Version {item.revision} ·{" "}
                  {new Date(item.recorded_at).toLocaleString()}
                </button>
              </li>
            ))}
          </ul>
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="versions"
        cursor={cursor}
        ready={state.phase === "ready"}
        next={state.phase === "ready" ? state.value.next_before_revision : null}
        change={(value) => {
          query.clear();
          setCursor(value as number | null);
        }}
      />
    </section>
  );
}
