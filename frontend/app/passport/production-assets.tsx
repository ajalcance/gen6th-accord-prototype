import { useEffect } from "react";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { GovernanceRead } from "./governance-common";
import { usePersonaQuery } from "./use-persona-query";

export function ProductionAssets({
  source,
  version,
  denied,
  children,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
  children: (assets: CampaignReceipt["assets"]) => React.ReactNode;
}) {
  const { state, query } = usePersonaQuery<CampaignReceipt["assets"]>();
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return (
    <section aria-label="Campaign asset setup">
      <h3>Production asset catalogue</h3>
      <p>
        An authorized asset catalogue for this exact version is required. Upload
        and inspect permitted bytes, then explicitly register them in the
        private evidence panel.
      </p>
      {source.passports && (
        <button
          className="secondary"
          disabled={state.phase === "loading"}
          onClick={() =>
            void query.run((signal) =>
              source.passports!.assets(version.version_id, signal),
            )
          }
        >
          Load production assets
        </button>
      )}
      <GovernanceRead
        state={state}
        query={query}
        resource="Production asset catalogue"
      >
        {(assets) =>
          assets.length ? (
            children(assets)
          ) : (
            <p>
              No authorized assets registered for this version. Studio catalogue
              setup is required.
            </p>
          )
        }
      </GovernanceRead>
    </section>
  );
}
