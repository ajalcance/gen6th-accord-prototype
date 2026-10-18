import { useState } from "react";
import type { PublicationGateway } from "../../lib/persona-publications";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceRead } from "./governance-common";
import { useGovernanceAccess } from "./saved-governance-read";
import PassportShare from "./passport-share";

export default function PublicationHistory({
  gateway,
  campaign,
}: {
  gateway: PublicationGateway;
  campaign: string;
}) {
  const { query, state } =
    usePersonaQuery<Awaited<ReturnType<PublicationGateway["history"]>>>();
  const [cursor, setCursor] = useState<string | null>(null);
  useGovernanceAccess(state.phase);
  function load(after: string | null) {
    setCursor(after);
    void query.run((signal) => gateway.history(campaign, after, signal));
  }
  return (
    <section aria-label="Public approval history">
      <h4>Saved public approvals</h4>
      <button disabled={state.phase === "loading"} onClick={() => load(cursor)}>
        Refresh public approval history
      </button>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            {page.items.length === 0 && (
              <p>No public approvals on this page.</p>
            )}
            {page.items.map((item) => (
              <article key={item.receipt.publication_id}>
                <p>
                  {item.withdrawn
                    ? "Public access withdrawn"
                    : "Public field approval recorded"}
                </p>
                {!item.withdrawn && (
                  <>
                    <PassportShare path={item.receipt.path} />
                    <button
                      onClick={() =>
                        void query.run(async (signal) => {
                          await gateway.unpublish(
                            item.receipt.publication_id,
                            signal,
                          );
                          return gateway.history(campaign, cursor, signal);
                        })
                      }
                    >
                      Withdraw this public approval
                    </button>
                  </>
                )}
              </article>
            ))}
            <button disabled={cursor === null} onClick={() => load(null)}>
              First approval page
            </button>
            <button
              disabled={page.next === null}
              onClick={() => load(page.next)}
            >
              Next approval page
            </button>
          </>
        )}
      </GovernanceRead>
    </section>
  );
}
