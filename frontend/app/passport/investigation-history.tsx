import { useEffect, useState, type ReactNode } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { InvestigationPage } from "../../lib/persona-investigation-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceRead, HistoryPager } from "./governance-common";
import InvestigationFindings from "./investigation-findings";
import PreparedReviewWrite from "./prepared-review-write";
import SavedGovernanceReviews from "./saved-governance-reviews";
import RequestInvestigationReview, {
  InvestigationReviewRequests,
} from "./investigation-review-request";

function useHistory(
  source: SavedPersonaSource,
  version: PersonaVersion,
  denied: () => void,
) {
  const [cursor, setCursor] = useState<number | null>(null);
  const { query, state } = usePersonaQuery<InvestigationPage>();
  useEffect(() => {
    if (source.investigations)
      void query.run((signal) =>
        source.investigations!.history(version.version_id, cursor, signal),
      );
    return () => query.stop();
  }, [source, version.version_id, cursor, query]);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return { query, state, cursor, setCursor };
}
export default function InvestigationHistory({
  source,
  version,
  denied,
  includeReview = true,
  action,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
  includeReview?: boolean;
  action?: ReactNode;
}) {
  const { query, state, cursor, setCursor } = useHistory(
    source,
    version,
    denied,
  );
  return (
    <section className="workflow-section" aria-label="Investigation history">
      <div className="workflow-section-heading">
        <h3>Investigations</h3>
        {action}
      </div>
      {!source.investigations && (
        <p>Investigation history is unavailable on this connection.</p>
      )}
      <GovernanceRead
        state={state}
        query={query}
        resource="Investigation history"
      >
        {(page) => <HistoryItems page={page} source={source} denied={denied} />}
      </GovernanceRead>
      <HistoryPager
        noun="investigations"
        cursor={cursor}
        state={state}
        setCursor={(value) => {
          query.clear();
          setCursor(value);
        }}
      />
      {includeReview && (
        <>
          <IndependentReview
            source={source}
            version={version}
            denied={denied}
          />
          <InvestigationReviewRequests
            source={source}
            version={version.version_id}
            denied={denied}
          />
        </>
      )}
    </section>
  );
}
function HistoryItems({
  page,
  source,
  denied,
}: {
  page: InvestigationPage;
  source: SavedPersonaSource;
  denied: () => void;
}) {
  return (
    <>
      {page.items.length === 0 && (
        <p>No investigation findings for this exact version.</p>
      )}
      {page.items.map((item) => (
        <details key={item.id}>
          <summary>
            Analysis #{item.ordinal} · {item.recorded_at}
          </summary>
          <InvestigationFindings result={item} />
          <RequestInvestigationReview
            source={source}
            packet={item}
            denied={denied}
          />
        </details>
      ))}
    </>
  );
}
export function IndependentReview({
  source,
  version,
  denied,
}: {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
}) {
  return (
    <details>
      <summary>Prepare independent human review</summary>
      <p className="help">
        Give the reviewer the exact version and analysis ID. This opens the
        existing decision workflow. A saved request appears separately below; it
        does not create an approval. The server requires a currently authorized
        independent human reviewer. Cite the analysis ID in the review
        statement.
      </p>
      {source.writeGateway && (
        <PreparedReviewWrite
          source={source}
          version={version}
          denied={denied}
        />
      )}
      <SavedGovernanceReviews gateway={source.gateway} version={version} />
    </details>
  );
}
