import { VersionPicker } from "./version-picker";
import { ReviewRow } from "../../app/passport/review-row";
import { useEffect, useState } from "react";
import type {
  ReviewReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type { DecisionPage } from "../../lib/persona-read-contracts";
import { requireContract } from "../../lib/persona-validation";
import { EXAMPLE_VERSIONS } from "./governance-fixtures";
import {
  GovernanceEmpty,
  GovernanceRead,
  HistoryPager,
} from "../../app/passport/governance-common";
import { usePersonaQuery } from "../../app/passport/use-persona-query";

type Props = { gateway: PersonaGateway };
export default function GovernanceReviews({ gateway }: Props) {
  const [revision, setRevision] = useState(2);
  const [cursor, setCursor] = useState<number | null>(null);
  const version = EXAMPLE_VERSIONS.find((row) => row.revision === revision)!;
  const { state, query } = useReviewHistory(gateway, version, cursor);
  return (
    <section
      aria-label="Independent review history"
      className="governance-section"
    >
      <ReviewHeading
        revision={revision}
        change={(value) => {
          setCursor(null);
          setRevision(value);
        }}
      />
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            {page.items.length === 0 && (
              <GovernanceEmpty title="No independent review yet">
                Request review of this exact version once a verified reviewer
                connection is available. Earlier reviews stay in their original
                version history.
              </GovernanceEmpty>
            )}
            {page.items.map((row) => (
              <ReviewRow
                key={row.id}
                gateway={gateway}
                row={row}
                revision={revision}
              />
            ))}
          </>
        )}
      </GovernanceRead>
      <HistoryPager
        cursor={cursor}
        state={state}
        setCursor={setCursor}
        noun="reviews"
      />
    </section>
  );
}

function useReviewHistory(
  gateway: PersonaGateway,
  version: PersonaVersion,
  cursor: number | null,
) {
  const read = usePersonaQuery<DecisionPage<ReviewReceipt>>();
  const { query } = read;
  useEffect(() => {
    void query.run(async (signal) => {
      const page = await gateway.reads.reviewHistory(
        version.version_id,
        { before_ordinal: cursor, limit: 1 },
        signal,
      );
      requireContract(
        page.items.every((row) => row.reviewer_ref !== version.creator_ref),
      );
      return page;
    });
    return () => query.clear();
  }, [gateway, version, cursor, query]);
  return read;
}

function ReviewHeading({
  revision,
  change,
}: {
  revision: number;
  change: (value: number) => void;
}) {
  return (
    <div className="governance-heading">
      <div>
        <h3>Independent review history</h3>
        <p className="help">
          A distinct fictional reviewer. Historical approval does not approve a
          newer version or establish rights.
        </p>
      </div>
      <VersionPicker
        label="Reviewed version"
        revision={revision}
        change={change}
      />
    </div>
  );
}

export { ReviewRow } from "../../app/passport/review-row";
