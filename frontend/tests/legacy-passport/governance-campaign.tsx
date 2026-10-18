import { DecisionRow } from "../../app/passport/campaign-decision-row";
import { useEffect, useState } from "react";
import type {
  CampaignStatus,
  DecisionReceipt,
} from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import type { DecisionPage } from "../../lib/persona-read-contracts";
import { EXAMPLE_CAMPAIGN } from "./governance-fixtures";
import {
  RecordedTime,
  GovernanceEmpty,
  GovernanceRead,
  HistoryPager,
} from "../../app/passport/governance-common";
import { usePersonaQuery } from "../../app/passport/use-persona-query";

export default function GovernanceCampaign({
  gateway,
  empty,
}: {
  gateway: PersonaGateway;
  empty: boolean;
}) {
  const { state, query } = usePersonaQuery<CampaignStatus>();
  useEffect(() => {
    if (!empty)
      void query.run((signal) =>
        gateway.campaignStatus(EXAMPLE_CAMPAIGN.id, signal),
      );
    return () => query.clear();
  }, [gateway, empty, query]);
  if (empty)
    return (
      <GovernanceEmpty title="No campaign offer">
        Define the purpose, recipient, assets and time window after independent
        review. A verified connection is required to record an offer.
      </GovernanceEmpty>
    );
  return (
    <section aria-label="Campaign decisions" className="governance-section">
      <h3>Campaign scope & decisions</h3>
      <GovernanceRead state={state} query={query}>
        {(value) => <CampaignScope status={value} />}
      </GovernanceRead>
      <CampaignHistory gateway={gateway} />
    </section>
  );
}

function CampaignScope({ status }: { status: CampaignStatus }) {
  const scope = status.receipt.scope;
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h3>{scope.name}</h3>
        <span className="status warning">Use blocked</span>
      </div>
      <p>
        Revoked · newer version exists. Historical acceptance does not authorize
        current use.
      </p>
      <p className="help">
        Version 2 · evaluated at frozen example time{" "}
        <RecordedTime value={status.evaluated_at} />
      </p>
      <dl className="governance-fields governance-columns">
        <div>
          <dt>Recipient</dt>
          <dd>{scope.recipient_ref}</dd>
        </div>
        <div>
          <dt>Purpose</dt>
          <dd>{scope.purpose}</dd>
        </div>
        <div>
          <dt>Conditions</dt>
          <dd>{scope.conditions}</dd>
        </div>
        <div>
          <dt>Time window</dt>
          <dd>
            <RecordedTime value={scope.starts_at} /> →{" "}
            <RecordedTime value={scope.ends_at} />
          </dd>
        </div>
      </dl>
      <CampaignReferences status={status} />
    </article>
  );
}

function CampaignHistory({ gateway }: { gateway: PersonaGateway }) {
  const [cursor, setCursor] = useState<number | null>(null);
  const { state, query } = usePersonaQuery<DecisionPage<DecisionReceipt>>();
  useEffect(() => {
    void query.run((signal) =>
      gateway.reads.campaignHistory(
        EXAMPLE_CAMPAIGN.id,
        { before_ordinal: cursor, limit: 2 },
        signal,
      ),
    );
    return () => query.clear();
  }, [gateway, cursor, query]);
  return (
    <>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            <h3>Decision history</h3>
            {page.items.length === 0 && (
              <GovernanceEmpty title="No campaign decisions">
                Recipient acceptance is still required. An offer alone does not
                authorize use.
              </GovernanceEmpty>
            )}
            {page.items.map((row) => (
              <DecisionRow
                key={row.id}
                row={row}
                gateway={gateway}
                versionId={EXAMPLE_CAMPAIGN.version_id}
              />
            ))}
          </>
        )}
      </GovernanceRead>
      <HistoryPager
        cursor={cursor}
        state={state}
        setCursor={setCursor}
        noun="decisions"
      />
    </>
  );
}

export { DecisionRow } from "../../app/passport/campaign-decision-row";
function CampaignReferences({ status }: { status: CampaignStatus }) {
  return (
    <details>
      <summary>Referenced assets & review</summary>
      <p className="help">
        Campaign assets are separate from temporary private evidence.
      </p>
      <dl className="governance-fields">
        <div>
          <dt>Review ID</dt>
          <dd>{status.receipt.review_id}</dd>
        </div>
        {status.receipt.assets.map((asset) => (
          <div key={asset.id}>
            <dt>{asset.label}</dt>
            <dd>{asset.digest}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
