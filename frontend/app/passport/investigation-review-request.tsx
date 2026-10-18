import { useEffect, useState } from "react";
import type {
  ReviewRequestPage,
  ReviewRequestReceipt,
} from "../../lib/persona-investigation-reviews";
import type { InvestigationResult } from "../../lib/persona-investigation-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceRead, HistoryPager } from "./governance-common";
import { ReadFeedback } from "./saved-record";

export default function RequestInvestigationReview({
  source,
  packet,
  denied,
}: {
  source: SavedPersonaSource;
  packet: InvestigationResult;
  denied: () => void;
}) {
  const { query, state } = usePersonaQuery<ReviewRequestReceipt>();
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  if (!source.investigations) return null;
  const request = () => {
    const command = {
      request_id: crypto.randomUUID(),
      version_id: packet.version_id,
      investigation_id: packet.id,
    };
    void query.run((signal) =>
      source.investigations!.requestReview(command, signal),
    );
  };
  return (
    <section aria-label="Request investigation review">
      <p className="help">
        Save an internal independent review request for this exact version and
        analysis. New requests require the current version. A request does not
        approve use or send a notification.
      </p>
      <button
        className="secondary"
        disabled={state.phase !== "idle"}
        onClick={request}
      >
        Request independent review
      </button>
      <RequestFeedback read={{ query, state }} />
    </section>
  );
}
function RequestFeedback({
  read: { query, state },
}: {
  read: ReturnType<typeof usePersonaQuery<ReviewRequestReceipt>>;
}) {
  return (
    <>
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && (
        <p role="status">
          Review requested · request {state.value.id} · analysis{" "}
          {state.value.investigation_id}. Await an independent human decision.
        </p>
      )}
      {state.phase === "cancelled" && (
        <p>
          The server may have saved this request. Retry the same intent or
          inspect review request history.
        </p>
      )}
    </>
  );
}
function useReviewRequests(
  source: SavedPersonaSource,
  version: string,
  denied: () => void,
) {
  const { query, state } = usePersonaQuery<ReviewRequestPage>();
  const [cursor, setCursor] = useState<number | null>(null);
  useEffect(() => {
    if (source.investigations)
      void query.run((signal) =>
        source.investigations!.reviewRequests(version, cursor, signal),
      );
    return () => query.stop();
  }, [source, version, cursor, query]);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return { query, state, cursor, setCursor };
}
export function InvestigationReviewRequests({
  source,
  version,
  denied,
}: {
  source: SavedPersonaSource;
  version: string;
  denied: () => void;
}) {
  const { query, state, cursor, setCursor } = useReviewRequests(
    source,
    version,
    denied,
  );
  return (
    <section
      className="workflow-section"
      aria-label="Independent review request history"
    >
      <div className="workflow-section-heading">
        <h3>Review requests</h3>
        <button
          className="secondary"
          disabled={state.phase !== "ready"}
          onClick={() => void query.retry()}
        >
          Refresh review requests
        </button>
      </div>
      {!source.investigations && (
        <p role="status">
          Review request history is unavailable on this connection.
        </p>
      )}
      <GovernanceRead state={state} query={query} resource="Review requests">
        {(page) => <RequestRows page={page} />}
      </GovernanceRead>
      <HistoryPager
        noun="review requests"
        cursor={cursor}
        state={state}
        setCursor={(value) => {
          query.clear();
          setCursor(value);
        }}
      />
      <p className="help">
        Requests remain historical receipts. Current reviewer decisions appear
        in independent review history.
      </p>
    </section>
  );
}
function RequestRows({ page }: { page: ReviewRequestPage }) {
  return (
    <>
      {page.items.length === 0 && (
        <p>No saved requests for this exact version.</p>
      )}
      <ul>
        {page.items.map((row) => (
          <li key={row.id}>
            Requested by {row.requester_ref} · {row.requested_at} · analysis{" "}
            {row.investigation_id} · request {row.id}
          </li>
        ))}
      </ul>
    </>
  );
}
