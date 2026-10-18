import { useCallback, useState } from "react";
import type {
  PersonaVersion,
  ReviewReceipt,
} from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import { requireContract } from "../../lib/persona-validation";
import {
  GovernanceEmpty,
  GovernanceRead,
  HistoryPager,
} from "./governance-common";
import { ReviewRow } from "./review-row";
import { useGovernanceRead } from "./saved-governance-read";

export default function SavedGovernanceReviews({
  gateway,
  version,
}: {
  gateway: PersonaGateway;
  version: PersonaVersion;
}) {
  const [cursor, setCursor] = useState<number | null>(null);
  const load = useCallback(
    async (signal: AbortSignal) => {
      const page = await gateway.reads.reviewHistory(
        version.version_id,
        { before_ordinal: cursor, limit: 20 },
        signal,
      );
      requireContract(
        page.items.every((row) => row.reviewer_ref !== version.creator_ref),
      );
      return page;
    },
    [gateway, version, cursor],
  );
  const { state, query } = useGovernanceRead(load);
  return (
    <section
      className="governance-section"
      aria-label="Saved independent reviews"
    >
      <h3>Review history</h3>
      <GovernanceRead
        state={state}
        query={query}
        resource="Independent review history"
      >
        {(page) => (
          <ReviewItems
            items={page.items}
            gateway={gateway}
            revision={version.revision}
          />
        )}
      </GovernanceRead>
      <HistoryPager
        cursor={cursor}
        state={state}
        setCursor={(value) => {
          query.clear();
          setCursor(value);
        }}
        noun="reviews"
      />
    </section>
  );
}

function ReviewItems({
  items,
  gateway,
  revision,
}: {
  items: ReviewReceipt[];
  gateway: PersonaGateway;
  revision: number;
}) {
  return (
    <>
      {items.length === 0 && (
        <GovernanceEmpty title="No independent review yet">
          Request review of this exact version once a verified review connection
          is available.
        </GovernanceEmpty>
      )}
      {items.map((row) => (
        <ReviewRow
          key={row.id}
          gateway={gateway}
          row={row}
          revision={revision}
        />
      ))}
    </>
  );
}
