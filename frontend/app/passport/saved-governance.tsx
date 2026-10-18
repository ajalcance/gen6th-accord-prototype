import { useCallback, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { GovernanceEmpty, GovernanceRead } from "./governance-common";
import { VersionSnapshot } from "./version-snapshot";
import { DiscoveryPager, useGovernanceRead } from "./saved-governance-read";
const governanceSections = ["Version", "Reviews", "Campaigns", "Evidence"];
import SavedGovernanceReviews from "./saved-governance-reviews";
import SavedGovernanceCampaigns from "./saved-governance-campaigns";
import SavedGovernanceEvidence from "./saved-governance-evidence";

export default function SavedGovernance({
  source,
  latest,
}: {
  source: SavedPersonaSource;
  latest: PersonaVersion;
}) {
  const [cursor, setCursor] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.governance.versions(
        latest.persona_id,
        { before_revision: cursor, limit: 20 },
        signal,
      ),
    [source.gateway, latest.persona_id, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section
      aria-label="Saved governance records"
      className="governance-section governance-workspace saved-governance"
    >
      <GovernanceHeading />
      <GovernanceRead state={state} query={query} resource="Version history">
        {(page) => (
          <VersionSelection
            items={page.items}
            selected={selected}
            change={setSelected}
            source={source}
            latest={latest}
          />
        )}
      </GovernanceRead>
      <DiscoveryPager
        noun="versions"
        cursor={cursor}
        ready={state.phase === "ready"}
        next={state.phase === "ready" ? state.value.next_before_revision : null}
        change={(value) => {
          query.clear();
          setSelected(null);
          setCursor(value as number | null);
        }}
      />
    </section>
  );
}

function GovernanceHeading() {
  return (
    <>
      <h3>Historical activity</h3>
      <p className="help">
        Browse recorded versions, reviews, campaigns and evidence below. This
        history selection does not change the performer version used by the
        other workspace pages.
      </p>
    </>
  );
}

function VersionSelection({
  items,
  selected,
  change,
  source,
  latest,
}: {
  items: PersonaVersion[];
  selected: string | null;
  change: (value: string) => void;
  source: SavedPersonaSource;
  latest: PersonaVersion;
}) {
  if (items.length === 0)
    return (
      <GovernanceEmpty title="No versions on this page">
        Return to the first page to inspect saved versions.
      </GovernanceEmpty>
    );
  const version = items.find((row) => row.version_id === selected) ?? items[0];
  return (
    <>
      <label>
        Saved version
        <select
          value={version.version_id}
          onChange={(event) => change(event.target.value)}
        >
          {items.map((row) => (
            <option key={row.version_id} value={row.version_id}>
              Version {row.revision}
              {row.revision === latest.revision
                ? " · loaded head"
                : row.revision > latest.revision
                  ? " · newer than loaded head"
                  : " · historical"}
            </option>
          ))}
        </select>
      </label>
      <VersionGovernance
        key={version.version_id}
        source={source}
        version={version}
      />
    </>
  );
}

function VersionGovernance({
  source,
  version,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
}) {
  const [section, setSection] = useState("Version");
  return (
    <>
      <nav
        className="governance-navigation"
        aria-label="Saved governance sections"
      >
        {governanceSections.map((label) => (
          <button
            className="secondary"
            key={label}
            aria-pressed={section === label}
            onClick={() => setSection(label)}
          >
            {label}
          </button>
        ))}
      </nav>
      {section === "Version" && <VersionSnapshot version={version} />}
      {section === "Reviews" && (
        <SavedGovernanceReviews gateway={source.gateway} version={version} />
      )}
      {section === "Campaigns" && (
        <SavedGovernanceCampaigns gateway={source.gateway} version={version} />
      )}
      {section === "Evidence" && (
        <SavedGovernanceEvidence gateway={source.gateway} version={version} />
      )}
    </>
  );
}
